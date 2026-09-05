"""
Authentication Routes: Register, Login, and Profile endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.base import get_db
from app.models.user import User, UserRole
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse
from app.schemas.inference import StandardResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=StandardResponse[TokenResponse], status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account."""
    # Check if user already exists
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "USER_EXISTS", "message": "An account with this email already exists."},
        )

    # First registered user becomes ADMIN automatically for easier setup
    count_res = await db.execute(select(func.count(User.id)))
    user_count = count_res.scalar() or 0
    assigned_role = UserRole.ADMIN if user_count == 0 else UserRole.USER

    hashed_pw = get_password_hash(payload.password)
    user = User(
        email=payload.email,
        hashed_password=hashed_pw,
        full_name=payload.full_name,
        role=assigned_role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    user_resp = UserResponse.model_validate(user)

    return StandardResponse(
        success=True,
        data=TokenResponse(access_token=token, user=user_resp),
        message="Account created successfully",
    )


@router.post("/login", response_model=StandardResponse[TokenResponse])
async def login(
    payload: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with email and password to obtain a JWT token."""
    res = await db.execute(select(User).where(User.email == payload.email))
    user = res.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password."},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "USER_DISABLED", "message": "This account has been disabled."},
        )

    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    user_resp = UserResponse.model_validate(user)

    return StandardResponse(
        success=True,
        data=TokenResponse(access_token=token, user=user_resp),
        message="Login successful",
    )


@router.get("/me", response_model=StandardResponse[UserResponse])
async def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve current authenticated user details."""
    return StandardResponse(
        success=True,
        data=UserResponse.from_orm(current_user),
        message="Profile retrieved successfully",
    )
