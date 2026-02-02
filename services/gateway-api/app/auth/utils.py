"""Authentication utilities (v0.8.0)"""

from datetime import datetime, timedelta, timezone
from typing import Annotated
import hashlib
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import User, APIKey

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ============================================================
# Password Utilities
# ============================================================

def hash_password(password: str) -> str:
    """비밀번호를 bcrypt로 해싱"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================
# JWT Utilities
# ============================================================

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Access token 생성"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    })
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict) -> str:
    """Refresh token 생성"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    })
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict | None:
    """토큰 디코딩 및 검증"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


# ============================================================
# API Key Utilities
# ============================================================

def generate_api_key() -> tuple[str, str, str]:
    """
    API Key 생성
    Returns: (full_key, key_hash, key_prefix)
    """
    # 32-byte random key
    raw_key = secrets.token_urlsafe(32)
    full_key = f"sk-proj-{raw_key}"

    # SHA-256 hash for storage
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()

    # Prefix for display (first 12 chars after "sk-proj-")
    key_prefix = f"sk-proj-{raw_key[:4]}"

    return full_key, key_hash, key_prefix


def hash_api_key(api_key: str) -> str:
    """API Key를 SHA-256으로 해싱"""
    return hashlib.sha256(api_key.encode()).hexdigest()


# ============================================================
# User Retrieval
# ============================================================

def get_user_by_email(db: Session, email: str) -> User | None:
    """이메일로 사용자 조회"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> User | None:
    """사용자명으로 사용자 조회"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """ID로 사용자 조회"""
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """사용자 인증 (이메일 + 비밀번호)"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# ============================================================
# Dependency Injection
# ============================================================

async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    api_key: Annotated[str | None, Depends(api_key_header)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    현재 인증된 사용자 반환 (JWT 또는 API Key)
    인증 실패 시 401 에러
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try JWT first
    if token:
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            user_id = payload.get("sub")
            if user_id:
                user = get_user_by_id(db, int(user_id))
                if user and user.is_active:
                    return user

    # Try API Key
    if api_key:
        key_hash = hash_api_key(api_key)
        api_key_obj = db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True,
        ).first()

        if api_key_obj:
            # Check expiration
            if api_key_obj.expires_at and api_key_obj.expires_at < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key has expired",
                )

            # Update usage stats
            api_key_obj.last_used_at = datetime.now(timezone.utc)
            api_key_obj.total_requests += 1
            db.commit()

            user = api_key_obj.user
            if user and user.is_active:
                return user

    raise credentials_exception


async def get_current_user_optional(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    api_key: Annotated[str | None, Depends(api_key_header)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    """
    현재 인증된 사용자 반환 (선택적)
    인증되지 않은 경우 None 반환
    """
    try:
        return await get_current_user(token, api_key, db)
    except HTTPException:
        return None


def require_role(required_roles: list[str]):
    """특정 역할이 필요한 엔드포인트를 위한 의존성"""
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_roles}. Your role: {current_user.role}"
            )
        return current_user
    return role_checker
