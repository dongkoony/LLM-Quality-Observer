"""Authentication module for v0.8.0"""

from .router import router as auth_router
from .utils import get_current_user, get_current_user_optional
from .schemas import UserResponse, TokenResponse

__all__ = [
    "auth_router",
    "get_current_user",
    "get_current_user_optional",
    "UserResponse",
    "TokenResponse",
]
