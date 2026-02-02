"""Authentication router (v0.8.0)"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import User, APIKey, AuditLog

from .schemas import (
    UserCreate,
    UserResponse,
    UserUpdate,
    PasswordChange,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    APIKeyCreate,
    APIKeyResponse,
    APIKeyCreateResponse,
)
from .utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    get_user_by_email,
    get_user_by_username,
    authenticate_user,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================
# Helper Functions
# ============================================================

def create_audit_log(
    db: Session,
    action: str,
    user_id: int | None = None,
    api_key_id: int | None = None,
    resource_type: str | None = None,
    resource_id: int | None = None,
    status: str = "success",
    error_message: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict | None = None,
):
    """감사 로그 생성"""
    audit_log = AuditLog(
        user_id=user_id,
        api_key_id=api_key_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
        error_message=error_message,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_=metadata or {},
    )
    db.add(audit_log)
    db.commit()
    return audit_log


def get_client_ip(request: Request) -> str | None:
    """클라이언트 IP 추출"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


# ============================================================
# Registration & Login
# ============================================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """
    새 사용자 등록

    - 이메일과 사용자명은 고유해야 함
    - 비밀번호는 8자 이상, 대소문자/숫자/특수문자 포함
    """
    # Check if email already exists
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if username already exists
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Create user
    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        role="viewer",  # Default role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Audit log
    create_audit_log(
        db=db,
        action="auth.register",
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )

    return user


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """
    로그인 및 JWT 토큰 발급

    - 성공 시 access_token과 refresh_token 반환
    - access_token: 1시간 유효
    - refresh_token: 30일 유효
    """
    user = authenticate_user(db, login_data.email, login_data.password)

    if not user:
        # Audit log for failed login
        create_audit_log(
            db=db,
            action="auth.login",
            status="failure",
            error_message="Invalid email or password",
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            metadata={"email": login_data.email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Create tokens
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    # Audit log
    create_audit_log(
        db=db,
        action="auth.login",
        user_id=user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login/form", response_model=TokenResponse)
def login_form(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """
    OAuth2 호환 로그인 (form data)

    - Swagger UI 등에서 사용
    - username 필드에 이메일 입력
    """
    login_data = LoginRequest(email=form_data.username, password=form_data.password)
    return login(login_data, request, db)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Refresh token으로 새 access token 발급
    """
    payload = decode_token(refresh_data.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new tokens
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        refresh_token=new_refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
def logout(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    로그아웃

    참고: JWT는 stateless이므로 서버에서 토큰을 무효화할 수 없음.
    클라이언트에서 토큰을 삭제해야 함.
    (토큰 블랙리스트는 Redis 도입 시 구현 예정)
    """
    # Audit log
    create_audit_log(
        db=db,
        action="auth.logout",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )

    return {"message": "Logged out successfully"}


# ============================================================
# User Management
# ============================================================

@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """현재 로그인된 사용자 정보 조회"""
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    user_data: UserUpdate,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """현재 사용자 정보 수정"""
    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name

    if user_data.metadata is not None:
        current_user.metadata_ = {**current_user.metadata_, **user_data.metadata}

    db.commit()
    db.refresh(current_user)

    # Audit log
    create_audit_log(
        db=db,
        action="user.update",
        user_id=current_user.id,
        resource_type="user",
        resource_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )

    return current_user


@router.put("/me/password")
def change_password(
    password_data: PasswordChange,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """비밀번호 변경"""
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.password_hash = hash_password(password_data.new_password)
    db.commit()

    # Audit log
    create_audit_log(
        db=db,
        action="user.password_change",
        user_id=current_user.id,
        resource_type="user",
        resource_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )

    return {"message": "Password changed successfully"}


# ============================================================
# API Key Management
# ============================================================

@router.get("/api-keys", response_model=list[APIKeyResponse])
def list_api_keys(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """현재 사용자의 API Key 목록 조회"""
    api_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.revoked_at.is_(None),
    ).all()
    return api_keys


@router.post("/api-keys", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    key_data: APIKeyCreate,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    새 API Key 생성

    ⚠️ API Key는 생성 시 한 번만 표시됩니다. 안전하게 저장하세요.
    """
    # Generate key
    full_key, key_hash, key_prefix = generate_api_key()

    # Calculate expiration
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=key_data.expires_in_days)

    # Create API key
    api_key = APIKey(
        user_id=current_user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=key_data.name,
        scopes=key_data.scopes,
        expires_at=expires_at,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    # Audit log
    create_audit_log(
        db=db,
        action="api_key.create",
        user_id=current_user.id,
        resource_type="api_key",
        resource_id=api_key.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )

    return APIKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        api_key=full_key,  # Only shown once!
        key_prefix=key_prefix,
        scopes=api_key.scopes,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@router.delete("/api-keys/{key_id}")
def revoke_api_key(
    key_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """API Key 폐기"""
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id,
    ).first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    api_key.is_active = False
    api_key.revoked_at = datetime.now(timezone.utc)
    db.commit()

    # Audit log
    create_audit_log(
        db=db,
        action="api_key.revoke",
        user_id=current_user.id,
        resource_type="api_key",
        resource_id=api_key.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )

    return {"message": "API key revoked successfully"}
