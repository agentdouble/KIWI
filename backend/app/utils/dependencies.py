from fastapi import Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Session
from app.models.user import User
from app.utils.auth import verify_token
import uuid

async def get_session_id(x_session_id: Optional[str] = Header(None)) -> str:
    """Récupérer le session ID depuis le header"""
    if not x_session_id:
        # Log pour déboguer
        print(f"ERROR: X-Session-ID header missing. Received headers: {x_session_id}")
        raise HTTPException(
            status_code=400, 
            detail="X-Session-ID header required. Please ensure the header is sent with your request."
        )
    return x_session_id

async def get_current_session(
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db)
) -> Session:
    """Récupérer la session complète depuis la base de données"""
    result = await db.execute(
        select(Session).where(Session.id == uuid.UUID(session_id))
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    return session

# Authentification JWT
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Récupérer l'utilisateur actuel depuis le token JWT"""
    token = credentials.credentials
    
    # Vérifier le token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Token invalide ou expiré"
        )
    
    # Récupérer l'utilisateur
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Token invalide: user_id manquant"
        )
    
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Utilisateur non trouvé"
        )
    
    return user