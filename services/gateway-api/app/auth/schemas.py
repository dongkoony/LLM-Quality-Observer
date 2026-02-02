"""Authentication schemas (v0.8.0)"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


# ============================================================
# User Schemas
# ============================================================

class UserCreate(BaseModel):
    """사용자 등록 요청"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(None, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserResponse(BaseModel):
    """사용자 정보 응답"""
    id: int
    email: str
    username: str
    full_name: str | None = None
    role: str
    is_active: bool
    is_verified: bool
    max_requests_per_hour: int
    max_cost_per_month_usd: Decimal
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """사용자 정보 수정"""
    full_name: str | None = None
    metadata: dict | None = None


class PasswordChange(BaseModel):
    """비밀번호 변경"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


# ============================================================
# Auth Schemas
# ============================================================

class LoginRequest(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str | None = None
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """토큰 갱신 요청"""
    refresh_token: str


class TokenData(BaseModel):
    """JWT 토큰 페이로드"""
    user_id: int
    email: str
    username: str
    role: str
    token_type: str = "access"  # "access" or "refresh"


# ============================================================
# API Key Schemas
# ============================================================

class APIKeyCreate(BaseModel):
    """API Key 생성 요청"""
    name: str = Field(..., min_length=1, max_length=128)
    scopes: list[str] = ["chat:read", "chat:write"]
    expires_in_days: int | None = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """API Key 응답 (목록 조회용)"""
    id: int
    name: str
    key_prefix: str
    scopes: list[str]
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    total_requests: int

    model_config = {"from_attributes": True}


class APIKeyCreateResponse(BaseModel):
    """API Key 생성 응답 (키 포함)"""
    id: int
    name: str
    api_key: str  # 생성 시 1회만 표시
    key_prefix: str
    scopes: list[str]
    expires_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# Audit Log Schemas
# ============================================================

class AuditLogResponse(BaseModel):
    """감사 로그 응답"""
    id: int
    user_id: int | None
    username: str | None = None
    action: str
    resource_type: str | None
    resource_id: int | None
    status: str
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """감사 로그 목록 응답"""
    logs: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
