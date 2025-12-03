from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, and_, delete
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.agent import Agent, AgentFavorite
from app.models.chat import Chat
from app.models.message import Message
from app.models.user import User
from app.schemas.agent import (
    AgentResponse,
    CreateAgentRequest,
    PopularAgentResponse,
    UpdateAgentRequest,
)
from app.utils.auth import get_optional_current_user, get_current_active_user
from app.services.rbac_service import (
    PERM_AGENT_CREATE,
    PERM_AGENT_DELETE_ANY,
    PERM_AGENT_DELETE_OWN,
    PERM_AGENT_UPDATE_ANY,
    PERM_AGENT_UPDATE_OWN,
    user_has_permission,
)
import uuid
from typing import List, Optional
from datetime import datetime, timedelta, timezone

router = APIRouter()

def agent_to_response(agent: Agent, is_favorite: bool = False) -> dict:
    """Convertir un agent en dictionnaire pour AgentResponse"""
    return {
        "id": str(agent.id),
        "name": agent.name,
        "description": agent.description,
        "system_prompt": agent.system_prompt,
        "avatar": agent.avatar,
        "avatar_image": agent.avatar_image,
        "capabilities": agent.capabilities or [],
        "category": agent.category,
        "tags": agent.tags or [],
        "is_public": agent.is_public,
        "created_by_trigramme": agent.user.trigramme if agent.user else None,
        "created_at": agent.created_at,
        "updated_at": agent.updated_at,
        "is_default": agent.is_default,
        "is_favorite": is_favorite,
    }

@router.get("/", response_model=List[AgentResponse])
async def get_agents(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Récupérer tous les agents visibles par l'utilisateur"""
    favorite_agent_ids: set[uuid.UUID] = set()
    if current_user:
        favorite_result = await db.execute(
            select(AgentFavorite.agent_id).where(AgentFavorite.user_id == current_user.id)
        )
        favorite_agent_ids = {row for row in favorite_result.scalars()}

    is_admin = bool(current_user and current_user.is_admin)

    if is_admin:
        result = await db.execute(
            select(Agent)
            .options(selectinload(Agent.user))
            .order_by(Agent.created_at.desc())
        )
    elif current_user:
        # User connecté : voir ses agents privés + tous les agents publics
        result = await db.execute(
            select(Agent).where(
                or_(
                    Agent.user_id == current_user.id,
                    Agent.is_public == True,
                )
            )
            .options(selectinload(Agent.user))
            .order_by(Agent.created_at.desc())
        )
    else:
        # User non connecté : voir seulement les agents publics
        result = await db.execute(
            select(Agent)
            .where(Agent.is_public == True)
            .options(selectinload(Agent.user))
            .order_by(Agent.created_at.desc())
        )
    
    agents = result.scalars().all()
    
    return [
        AgentResponse(**agent_to_response(agent, agent.id in favorite_agent_ids)) for agent in agents
    ]

@router.get("/defaults", response_model=List[AgentResponse])
async def get_default_agents(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Récupérer les agents par défaut"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    favorite_agent_ids: set[uuid.UUID] = set()
    favorite_result = await db.execute(
        select(AgentFavorite.agent_id).where(AgentFavorite.user_id == current_user.id)
    )
    favorite_agent_ids = {row for row in favorite_result.scalars()}

    result = await db.execute(
        select(Agent)
        .where(
            and_(
                Agent.is_default == True,
                Agent.user_id == current_user.id,
            )
        )
        .options(selectinload(Agent.user))
    )
    agents = result.scalars().all()
    
    return [
        AgentResponse(**agent_to_response(agent, agent.id in favorite_agent_ids)) for agent in agents
    ]

@router.get("/popular/weekly", response_model=List[PopularAgentResponse])
async def get_weekly_popular_agents(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Retourne le top 6 des agents les plus utilisés sur les 7 derniers jours.

    Note: Un "usage" correspond au nombre de conversations distinctes (Chat.id)
    ayant au moins un message utilisateur au cours des 7 derniers jours.
    """
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    usage_count = func.count(func.distinct(Chat.id)).label("weekly_usage_count")
    last_activity = func.max(Message.created_at).label("last_activity")

    favorite_agent_ids: set[uuid.UUID] = set()
    if current_user:
        favorite_result = await db.execute(
            select(AgentFavorite.agent_id).where(AgentFavorite.user_id == current_user.id)
        )
        favorite_agent_ids = {row for row in favorite_result.scalars()}

    stmt = (
        select(Agent, usage_count, last_activity)
        .join(Chat, Chat.agent_id == Agent.id)
        .join(
            Message,
            and_(
                Message.chat_id == Chat.id,
                Message.role == "user",
                # Limiter au messages des 7 derniers jours
                Message.created_at >= seven_days_ago,
            )
        )
        .where(
            and_(
                Agent.is_active == True,
                or_(Agent.is_public == True, Agent.is_default == True),
            )
        )
        .group_by(Agent.id)
        .order_by(usage_count.desc(), last_activity.desc())
        .options(selectinload(Agent.user))
    )

    result = await db.execute(stmt)
    popular_agents: List[PopularAgentResponse] = []
    weekly_ids: set[uuid.UUID] = set()

    MAX_RESULTS = 6
    for agent, weekly_usage_count, _ in result.all():
        # Ignorer les agents par défaut (assistant généraliste)
        if agent.is_default:
            continue

        payload = agent_to_response(agent, agent.id in favorite_agent_ids)
        payload["weekly_usage_count"] = int(weekly_usage_count)
        payload["usage_period"] = "weekly"
        popular_agents.append(PopularAgentResponse(**payload))
        weekly_ids.add(agent.id)

        if len(popular_agents) == MAX_RESULTS:
            break

    # Compléter avec les plus utilisés all-time si nécessaire
    if len(popular_agents) < MAX_RESULTS:
        total_usage_count = func.count(func.distinct(Chat.id)).label("total_usage_count")
        any_last_activity = func.max(Message.created_at).label("last_activity")

        stmt_alltime = (
            select(Agent, total_usage_count, any_last_activity)
            .join(Chat, Chat.agent_id == Agent.id)
            .join(
                Message,
                and_(
                    Message.chat_id == Chat.id,
                    Message.role == "user",
                )
            )
            .where(
                and_(
                    Agent.is_active == True,
                    or_(Agent.is_public == True, Agent.is_default == True),
                )
            )
            .group_by(Agent.id)
            .order_by(total_usage_count.desc(), any_last_activity.desc())
            .options(selectinload(Agent.user))
        )

        alltime_result = await db.execute(stmt_alltime)
        for agent, total_count, _ in alltime_result.all():
            if agent.is_default:
                continue
            if agent.id in weekly_ids:
                continue
            payload = agent_to_response(agent, agent.id in favorite_agent_ids)
            payload["weekly_usage_count"] = 0
            payload["total_usage_count"] = int(total_count)
            payload["usage_period"] = "all_time"
            popular_agents.append(PopularAgentResponse(**payload))
            if len(popular_agents) == MAX_RESULTS:
                break

    return popular_agents

@router.post("/", response_model=AgentResponse)
async def create_agent(
    request: CreateAgentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Créer un nouvel agent (nécessite une authentification)"""
    if not await user_has_permission(db, current_user, PERM_AGENT_CREATE):
        raise HTTPException(status_code=403, detail="You are not allowed to create agents")

    agent = Agent(
        name=request.name,
        description=request.description,
        system_prompt=request.system_prompt,
        avatar=request.avatar,
        avatar_image=request.avatar_image,
        capabilities=request.capabilities,
        category=request.category,
        tags=request.tags,
        is_public=request.is_public,
        user_id=current_user.id
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    
    await db.refresh(agent, ['user'])
    return AgentResponse(**agent_to_response(agent))

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Récupérer un agent spécifique"""
    result = await db.execute(
        select(Agent).where(Agent.id == uuid.UUID(agent_id)).options(selectinload(Agent.user))
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Vérifier les permissions
    is_admin = bool(current_user and current_user.is_admin)

    if not agent.is_public:
        if not current_user or (agent.user_id != current_user.id and not is_admin):
            raise HTTPException(status_code=403, detail="Access denied")
    
    is_favorite = False
    if current_user:
        favorite_result = await db.execute(
            select(AgentFavorite).where(
                AgentFavorite.user_id == current_user.id,
                AgentFavorite.agent_id == agent.id,
            )
        )
        is_favorite = favorite_result.scalar_one_or_none() is not None

    await db.refresh(agent, ['user'])
    return AgentResponse(**agent_to_response(agent, is_favorite))

@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    request: UpdateAgentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mettre à jour un agent (nécessite d'être le propriétaire)"""
    result = await db.execute(
        select(Agent).where(Agent.id == uuid.UUID(agent_id)).options(selectinload(Agent.user))
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    is_owner = agent.user_id == current_user.id
    can_update_own = await user_has_permission(db, current_user, PERM_AGENT_UPDATE_OWN)
    can_update_any = await user_has_permission(db, current_user, PERM_AGENT_UPDATE_ANY)

    if not ((is_owner and can_update_own) or can_update_any):
        raise HTTPException(status_code=403, detail="You are not allowed to update this agent")
    
    # Mettre � jour les champs fournis
    if request.name is not None:
        agent.name = request.name
    if request.description is not None:
        agent.description = request.description
    if request.system_prompt is not None:
        agent.system_prompt = request.system_prompt
    if request.avatar is not None:
        agent.avatar = request.avatar
    if request.avatar_image is not None:
        agent.avatar_image = request.avatar_image
    if request.capabilities is not None:
        agent.capabilities = request.capabilities
    if request.category is not None:
        agent.category = request.category
    if request.tags is not None:
        agent.tags = request.tags
    if request.is_public is not None:
        agent.is_public = request.is_public
    
    await db.commit()
    await db.refresh(agent)
    
    await db.refresh(agent, ['user'])
    return AgentResponse(**agent_to_response(agent))


@router.post("/{agent_id}/favorite")
async def favorite_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    agent_uuid = uuid.UUID(agent_id)
    result = await db.execute(
        select(Agent).where(Agent.id == agent_uuid).options(selectinload(Agent.user))
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    is_admin = bool(current_user and current_user.is_admin)

    if not agent.is_public and agent.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    existing_favorite = await db.execute(
        select(AgentFavorite).where(
            AgentFavorite.user_id == current_user.id,
            AgentFavorite.agent_id == agent_uuid,
        )
    )
    if existing_favorite.scalar_one_or_none():
        return {"is_favorite": True}

    favorite = AgentFavorite(user_id=current_user.id, agent_id=agent_uuid)
    db.add(favorite)
    await db.commit()
    return {"is_favorite": True}


@router.delete("/{agent_id}/favorite")
async def unfavorite_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    agent_uuid = uuid.UUID(agent_id)
    await db.execute(
        delete(AgentFavorite).where(
            AgentFavorite.user_id == current_user.id,
            AgentFavorite.agent_id == agent_uuid,
        )
    )
    await db.commit()
    return {"is_favorite": False}

@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Supprimer un agent (nécessite d'être le propriétaire)"""
    result = await db.execute(
        select(Agent).where(Agent.id == uuid.UUID(agent_id)).options(selectinload(Agent.user))
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    is_owner = agent.user_id == current_user.id
    can_delete_own = await user_has_permission(db, current_user, PERM_AGENT_DELETE_OWN)
    can_delete_any = await user_has_permission(db, current_user, PERM_AGENT_DELETE_ANY)

    if not ((is_owner and can_delete_own) or can_delete_any):
        raise HTTPException(status_code=403, detail="You are not allowed to delete this agent")
    
    await db.delete(agent)
    await db.commit()
    
    return {"message": "Agent deleted successfully"}
