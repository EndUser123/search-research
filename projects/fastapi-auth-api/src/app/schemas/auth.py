"""
Pydantic schemas for authentication API.

Test Case ID: TC-SCHEMAS-001
Priority: High
Test Type: Schema Definition

Purpose:
Define request and response schemas with comprehensive validation,
serialization, and documentation for the authentication API.

Algorithm Approach: Pydantic models with validation and security
Time Complexity: O(1) - Schema validation
Space Complexity: O(1) - Schema object creation

Security Considerations:
- Input validation and sanitization
- Password field exclusion in responses
- Email format validation
- SQL injection prevention through proper types
"""

import logging
import re
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


class UserRegistrationRequest(BaseModel):
    """
    User registration request schema.

    Design Pattern: Request model with comprehensive validation
    Validates user registration input with security considerations.

    Security Considerations:
    - Email validation and normalization
    - Password strength validation
    - Input sanitization
    - SQL injection prevention
    """

    email: EmailStr = Field(
        ..., description="User email address", example="user@example.com"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password with strength requirements",
        example="SecurePass123!",
    )
    full_name: str | None = Field(
        None, max_length=255, description="User's full name", example="John Doe"
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password strength requirements.

        Algorithm Approach: Regex-based strength validation
        Time Complexity: O(1) - String analysis
        Space Complexity: O(1) - Constant space

        Security Considerations:
        - Minimum length enforcement
        - Character class diversity requirement
        - Common password pattern prevention

        Args:
        v: Password string to validate

        Returns:
        str: Validated password

        Raises:
        ValueError: If password doesn't meet strength requirements
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Check for uppercase, lowercase, digit, and special character
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)

        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                "Password must contain uppercase, lowercase, digit, and special character"
            )

        # Check for common weak patterns
        if "password" in v.lower() or "123456" in v:
            raise ValueError("Password cannot contain common patterns")

        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str | None) -> str | None:
        """
        Validate full name format.

        Security Considerations:
        - Prevents script injection
        - Allows valid name characters
        - Length validation

        Args:
        v: Full name to validate

        Returns:
        Optional[str]: Validated full name
        """
        if v is None:
            return v

        # Remove extra whitespace
        v = " ".join(v.split())

        # Basic validation - allow letters, spaces, hyphens, apostrophes
        if not re.match(r"^[a-zA-Z\s\-\'\.]+$", v):
            raise ValueError("Full name contains invalid characters")

        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "full_name": "John Doe",
            }
        }
    }


class UserLoginRequest(BaseModel):
    """
    User login request schema.

    Design Pattern: Authentication request model
    Handles user login with proper validation.

    Security Considerations:
    - Email validation
    - Password field handling
    - Rate limiting preparation
    """

    email: EmailStr = Field(
        ..., description="User email address", example="user@example.com"
    )
    password: str = Field(..., description="User password", example="SecurePass123!")

    @field_validator("password")
    @classmethod
    def validate_password_not_empty(cls, v: str) -> str:
        """
        Validate password is not empty.

        Args:
        v: Password to validate

        Returns:
        str: Validated password

        Raises:
        ValueError: If password is empty
        """
        if not v.strip():
            raise ValueError("Password cannot be empty")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {"email": "user@example.com", "password": "SecurePass123!"}
        }
    }


class TokenResponse(BaseModel):
    """
    JWT token response schema.

    Design Pattern: Authentication response model
    Returns JWT tokens with proper metadata.

    Security Considerations:
    - Token type specification
    - Expiration information
    - No sensitive data leakage
    """

    access_token: str = Field(
        ...,
        description="JWT access token",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    )
    refresh_token: str | None = Field(
        None,
        description="JWT refresh token for token renewal",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    )
    token_type: str = Field(
        default="bearer", description="Token type", example="bearer"
    )
    expires_in: int | None = Field(
        None, description="Token expiration time in seconds", example=1800
    )
    user: Optional["UserResponse"] = Field(
        None, description="Authenticated user information"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {"id": 1, "email": "user@example.com", "full_name": "John Doe"},
            }
        }
    }


class TokenRefreshRequest(BaseModel):
    """
    Token refresh request schema.

    Design Pattern: Token renewal request model
    Handles refresh token submission.

    Security Considerations:
    - Refresh token validation
    - Token rotation support
    """

    refresh_token: str = Field(
        ...,
        description="Refresh token to exchange for new access token",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    )

    model_config = {
        "json_schema_extra": {
            "example": {"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
        }
    }


class UserResponse(BaseModel):
    """
    User response schema.

    Design Pattern: User data model for API responses
    Excludes sensitive information from user data.

    Security Considerations:
    - Password hash exclusion
    - Sensitive field filtering
    - Data sanitization
    """

    id: int = Field(..., description="User ID", example=1)
    email: EmailStr = Field(
        ..., description="User email address", example="user@example.com"
    )
    full_name: str | None = Field(
        None, description="User's full name", example="John Doe"
    )
    avatar_url: str | None = Field(
        None, description="User's avatar URL", example="https://example.com/avatar.jpg"
    )
    is_active: bool = Field(
        ..., description="Whether the user account is active", example=True
    )
    is_verified: bool = Field(
        ..., description="Whether the user email is verified", example=False
    )
    is_admin: bool = Field(
        ..., description="Whether the user has admin privileges", example=False
    )
    two_factor_enabled: bool = Field(
        ..., description="Whether two-factor authentication is enabled", example=False
    )
    created_at: datetime | None = Field(
        None, description="Account creation timestamp", example="2023-01-01T00:00:00Z"
    )
    updated_at: datetime | None = Field(
        None, description="Last update timestamp", example="2023-01-01T00:00:00Z"
    )
    last_login_at: datetime | None = Field(
        None, description="Last login timestamp", example="2023-01-01T12:00:00Z"
    )

    model_config = {
        "from_attributes": True,  # For SQLAlchemy model compatibility
        "json_schema_extra": {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "John Doe",
                "avatar_url": "https://example.com/avatar.jpg",
                "is_active": True,
                "is_verified": False,
                "is_admin": False,
                "two_factor_enabled": False,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "last_login_at": "2023-01-01T12:00:00Z",
            }
        }
    }


class TokenValidationResponse(BaseModel):
    """
    Token validation response schema.

    Design Pattern: Token validation result model
    Returns token validation status and metadata.

    Security Considerations:
    - Validation status only
    - No sensitive token payload exposure
    - Clear validity indication
    """

    valid: bool = Field(..., description="Whether the token is valid", example=True)
    payload: dict[str, Any] | None = Field(
        None,
        description="Token payload (only for valid tokens)",
        example={"sub": "user@example.com", "exp": 1640995200},
    )
    user: UserResponse | None = Field(
        None, description="User information (only for valid tokens)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "valid": True,
                "payload": {
                    "sub": "user@example.com",
                    "exp": 1640995200,
                    "iat": 1640991600,
                    "type": "access",
                },
                "user": {"id": 1, "email": "user@example.com", "full_name": "John Doe"},
            }
        }
    }


class PasswordChangeRequest(BaseModel):
    """
    Password change request schema.

    Design Pattern: Password update request model
    Handles secure password changes.

    Security Considerations:
    - Current password verification
    - New password strength validation
    - Password confirmation
    """

    current_password: str = Field(
        ...,
        description="Current password for verification",
        example="OldSecurePass123!",
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password",
        example="NewSecurePass123!",
    )
    confirm_password: str = Field(
        ..., description="Password confirmation", example="NewSecurePass123!"
    )

    @model_validator(mode="after")
    def passwords_match(self) -> "PasswordChangeRequest":
        """
        Validate that new password and confirmation match.

        Security Considerations:
        - Prevents typos in password changes
        - Ensures password consistency

        Args:
        self: The model instance

        Returns:
        PasswordChangeRequest: Validated model instance

        Raises:
        ValueError: If passwords don't match
        """
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        """
        Validate new password strength.

        Security Considerations:
        - Same strength requirements as registration
        - Prevents weak password adoption

        Args:
        v: New password to validate

        Returns:
        str: Validated new password
        """
        # Reuse the same validation as registration
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)

        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                "Password must contain uppercase, lowercase, digit, and special character"
            )

        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "current_password": "OldSecurePass123!",
                "new_password": "NewSecurePass123!",
                "confirm_password": "NewSecurePass123!",
            }
        }
    }


class EmailVerificationRequest(BaseModel):
    """
    Email verification request schema.

    Design Pattern: Email verification model
    Handles email verification token submission.

    Security Considerations:
    - Token validation
    - Email confirmation
    """

    token: str = Field(
        ..., description="Email verification token", example="abc123def456..."
    )

    model_config = {
        "json_schema_extra": {"example": {"token": "abc123def456..."}}
    }


class PasswordResetRequest(BaseModel):
    """
    Password reset request schema.

    Design Pattern: Password reset model
    Handles password reset token submission.

    Security Considerations:
    - Token validation
    - New password requirements
    - Token single-use enforcement
    """

    token: str = Field(
        ..., description="Password reset token", example="def789ghi012..."
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password",
        example="NewSecurePass123!",
    )
    confirm_password: str = Field(
        ..., description="Password confirmation", example="NewSecurePass123!"
    )

    @model_validator(mode="after")
    def passwords_match(self) -> "PasswordResetRequest":
        """
        Validate that passwords match.

        Args:
        self: The model instance

        Returns:
        PasswordResetRequest: Validated model instance

        Raises:
        ValueError: If passwords don't match
        """
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate new password strength.

        Args:
        v: New password to validate

        Returns:
        str: Validated new password
        """
        # Same validation as other password fields
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)

        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                "Password must contain uppercase, lowercase, digit, and special character"
            )

        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "def789ghi012...",
                "new_password": "NewSecurePass123!",
                "confirm_password": "NewSecurePass123!",
            }
        }
    }


class ErrorResponse(BaseModel):
    """
    Standard error response schema.

    Design Pattern: Error response model
    Provides consistent error response format.

    Security Considerations:
    - Generic error messages
    - No sensitive information exposure
    - Consistent format for client handling
    """

    detail: str = Field(
        ..., description="Error description", example="Authentication failed"
    )
    error_code: str | None = Field(
        None, description="Machine-readable error code", example="AUTH_FAILED"
    )
    field: str | None = Field(
        None,
        description="Field that caused the error (for validation errors)",
        example="email",
    )
    retry_after: int | None = Field(
        None, description="Seconds to wait before retry (for rate limiting)", example=60
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "Authentication failed",
                "error_code": "AUTH_FAILED",
                "field": None,
                "retry_after": None,
            }
        }
    }
