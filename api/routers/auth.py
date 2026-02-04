from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.session import get_db
from database.user_crud import UserDB
from security.auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    Token,
    create_access_token,
)
from security.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=Token)
async def register(payload: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = UserDB.get_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    user = UserDB.create(
        db=db,
        email=payload.email,
        name=payload.name,
        password=payload.password,
    )

    # Generate token
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        name=user.name,
        is_admin=user.is_admin,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user).dict(),
    }

@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password"""
    # Verify credentials
    user = UserDB.verify_credentials(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Generate token
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        name=user.name,
        is_admin=user.is_admin,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user).dict(),
    }

@router.get("/verify")
async def verify(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Verify and return current user info"""
    user = UserDB.get_by_id(db, current_user.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "user": UserResponse.from_orm(user).dict(),
    }

@router.post("/logout")
async def logout(current_user = Depends(get_current_user)):
    """Logout (token is invalidated on client side)"""
    return {"message": "Logged out successfully"}
