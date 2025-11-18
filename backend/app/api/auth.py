from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from app.utils.auth import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    get_current_active_user
)
from app.utils.rate_limit import limiter, AUTH_RATE_LIMIT
from datetime import timedelta
import logging

router = APIRouter(tags=["authentication"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def register(request: Request, user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if len(user_data.trigramme) != 3 or not user_data.trigramme.isalpha():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le trigramme doit contenir exactement 3 lettres"
        )
    
    result = await db.execute(select(User).filter(User.trigramme == user_data.trigramme.upper()))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce trigramme est déjà utilisé"
        )
    
    user = User(email=user_data.email, trigramme=user_data.trigramme.upper())
    user.set_password(user_data.password)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"New user registered: {user.email}")
    return user


@router.post("/login", response_model=Token)
@limiter.limit(AUTH_RATE_LIMIT)
async def login(request: Request, user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    # Ignorer complètement tout token existant pour le login
    # On veut forcer un nouveau login local
    if "@" in user_data.identifier:
        result = await db.execute(select(User).filter(User.email == user_data.identifier))
    else:
        result = await db.execute(select(User).filter(User.trigramme == user_data.identifier.upper()))
    
    user = result.scalar_one_or_none()
    if not user or not user.check_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    logger.info(f"User logged in: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Successfully logged out"}