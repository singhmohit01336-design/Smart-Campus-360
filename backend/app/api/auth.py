from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    roll_id = (user_data.roll_number or user_data.institutional_id or "").strip()

    # 1. Determine institutional ID & email
    if roll_id:
        existing_id = db.scalar(
            select(User).where(User.institutional_id.ilike(roll_id))
        )
        if existing_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="College Roll Number or Institutional ID already registered.",
            )

    target_email = user_data.email
    if not target_email:
        if roll_id:
            target_email = f"{roll_id.lower()}@smartcampus360.edu"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either College Roll Number or Email is required for registration.",
            )

    # 2. Check for duplicate email
    existing_user = db.scalar(
        select(User).where(User.email.ilike(target_email))
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # 3. Public registration strictly enforces student role
    new_user = User(
        full_name=user_data.full_name.strip(),
        email=target_email.strip().lower(),
        institutional_id=roll_id.upper() if roll_id else None,
        hashed_password=hash_password(user_data.password),
        role=UserRole.STUDENT.value,
        phone_number=user_data.phone_number,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    login_key = (credentials.identifier or credentials.email or "").strip()
    if not login_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Roll Number, Institutional ID, or Email is required.",
        )

    user = db.scalar(
        select(User).where(
            or_(
                User.email.ilike(login_key),
                User.institutional_id.ilike(login_key),
            )
        )
    )

    if not user or not verify_password(
        credentials.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "role": user.role,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user
