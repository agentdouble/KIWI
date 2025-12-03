import logging
import secrets
from typing import Dict, List

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.agent import Agent
from app.models.user import User

FORCE_POWERPOINT_MARKER = "force_powerpoint_tool"
SYSTEM_USER_EMAIL = "foyergpt-system@foyer.lu"
SYSTEM_USER_TRIGRAM = "SYS"

_POWERPOINT_SYSTEM_PROMPT = (
    "Tu es PowerPoint Maestro, un agent officiel de FoyerGPT spécialisé dans la création de "
    "présentations professionnelles. Ton rôle est de transformer chaque demande en un PowerPoint "
    "complet en utilisant l'outil `generate_powerpoint_from_text`.\n\n"
    "Processus obligatoire :\n"
    "1. Clarifie si besoin le sujet, le public cible, le ton et le format attendu.\n"
    "2. Propose un plan synthétique (titres de sections et points clés) pour validation si des "
    "éléments manquent.\n"
    "3. Appelle obligatoirement l'outil `generate_powerpoint_from_text` avec un JSON structuré "
    "comprenant le titre de la présentation, l'objectif, le public cible et la liste des diapositives "
    "(titre + puces).\n"
    "4. Indique à l'utilisateur que la présentation est disponible via le lien généré.\n\n"
    "Ne rédige jamais toi-même la présentation finale et ne saute pas l'appel de l'outil. Si les "
    "informations sont insuffisantes pour produire un livrable de qualité, pose des questions "
    "ciblées avant d'utiliser l'outil."
)

OFFICIAL_AGENTS: List[Dict] = [
    {
        "name": "PowerPoint Maestro",
        "description": "Agent officiel qui convertit vos idées en présentations PowerPoint en un clic.",
        "system_prompt": _POWERPOINT_SYSTEM_PROMPT,
        "avatar": "📊",
        "avatar_image": None,
        "capabilities": ["powerpoint", "slides", FORCE_POWERPOINT_MARKER],
        "tags": ["official", "powerpoint", FORCE_POWERPOINT_MARKER],
        "category": "communication",
        "model": settings.openai_model,
        "is_default": False,
        "parameters": {
            "temperature": 0.2,
            "maxTokens": 4000,
            "topP": 0.9,
        },
    }
]


def _generate_secure_password() -> str:
    """Generate a random password for the system user."""
    return secrets.token_urlsafe(32)


def _normalize_sequence(values: List[str] | None) -> List[str]:
    return sorted((value or "").strip() for value in (values or []))


def _normalize_dict(payload: Dict | None) -> Dict:
    return payload or {}


def _sequences_differ(current: List[str] | None, expected: List[str] | None) -> bool:
    return _normalize_sequence(current) != _normalize_sequence(expected)


def _dicts_differ(current: Dict | None, expected: Dict | None) -> bool:
    return _normalize_dict(current) != _normalize_dict(expected)


async def _ensure_system_user(session: AsyncSession) -> User:
    """Ensure the dedicated system user exists and return it."""
    logger = logging.getLogger(__name__)

    result = await session.execute(
        select(User).where(
            or_(
                User.trigramme == SYSTEM_USER_TRIGRAM,
                User.email == SYSTEM_USER_EMAIL,
            )
        )
    )
    user = result.scalar_one_or_none()
    if user:
        return user

    user = User(
        email=SYSTEM_USER_EMAIL,
        trigramme=SYSTEM_USER_TRIGRAM,
        is_active=True,
    )
    user.set_password(_generate_secure_password())
    session.add(user)
    await session.commit()
    await session.refresh(user)
    logger.info("Created system user %s", SYSTEM_USER_EMAIL)
    return user


async def ensure_official_agents(session: AsyncSession) -> None:
    """Create or update the official agents required by the platform."""
    logger = logging.getLogger(__name__)
    system_user = await _ensure_system_user(session)

    has_changes = False

    for config in OFFICIAL_AGENTS:
        result = await session.execute(select(Agent).where(Agent.name == config["name"]))
        agent = result.scalar_one_or_none()

        if agent:
            updated = False
            if agent.user_id != system_user.id:
                agent.user_id = system_user.id
                updated = True
            if agent.description != config["description"]:
                agent.description = config["description"]
                updated = True
            if agent.system_prompt != config["system_prompt"]:
                agent.system_prompt = config["system_prompt"]
                updated = True
            if agent.avatar != config.get("avatar"):
                agent.avatar = config.get("avatar")
                updated = True
            if agent.avatar_image != config.get("avatar_image"):
                agent.avatar_image = config.get("avatar_image")
                updated = True
            if _sequences_differ(agent.capabilities, config.get("capabilities")):
                agent.capabilities = config.get("capabilities")
                updated = True
            if _sequences_differ(agent.tags, config.get("tags")):
                agent.tags = config.get("tags")
                updated = True
            if agent.category != config.get("category"):
                agent.category = config.get("category")
                updated = True
            if agent.model != config.get("model"):
                agent.model = config.get("model")
                updated = True
            if agent.is_default != config.get("is_default", False):
                agent.is_default = config.get("is_default", False)
                updated = True
            if _dicts_differ(agent.parameters, config.get("parameters")):
                agent.parameters = config.get("parameters")
                updated = True
            if not agent.is_public:
                agent.is_public = True
                updated = True
            if not agent.is_active:
                agent.is_active = True
                updated = True

            if updated:
                has_changes = True
                logger.info("Updated official agent '%s'", agent.name)
        else:
            agent = Agent(
                name=config["name"],
                description=config["description"],
                system_prompt=config["system_prompt"],
                avatar=config.get("avatar"),
                avatar_image=config.get("avatar_image"),
                capabilities=config.get("capabilities"),
                category=config.get("category"),
                tags=config.get("tags"),
                model=config.get("model"),
                is_public=True,
                is_default=config.get("is_default", False),
                is_active=True,
                parameters=config.get("parameters"),
                user_id=system_user.id,
            )
            session.add(agent)
            has_changes = True
            logger.info("Created official agent '%s'", agent.name)

    if has_changes:
        await session.commit()
