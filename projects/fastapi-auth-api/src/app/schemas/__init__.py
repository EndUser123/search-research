"""
Pydantic schemas for FastAPI Authentication API

Test Case ID: TC-SCHEMAS-INIT-001
Priority: Medium
Test Type: Package Configuration

Purpose:
Request and response schemas for the authentication API.
"""

from .auth import (
    EmailVerificationRequest,
    ErrorResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    TokenRefreshRequest,
    TokenResponse,
    TokenValidationResponse,
    UserLoginRequest,
    UserRegistrationRequest,
    UserResponse,
)

__all__ = [
    "UserRegistrationRequest",
    "UserLoginRequest",
    "TokenResponse",
    "TokenRefreshRequest",
    "UserResponse",
    "TokenValidationResponse",
    "PasswordChangeRequest",
    "EmailVerificationRequest",
    "PasswordResetRequest",
    "ErrorResponse",
]
