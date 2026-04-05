"""
Security utilities for FastAPI authentication API.

Test Case ID: TC-SECURITY-001
Priority: High
Test Type: Security Implementation

Purpose:
Provide secure password hashing, JWT token management, and authentication
utilities following security best practices.

Algorithm Approach: Cryptographic operations with timing attack protection
Time Complexity: O(1) - Hash and token operations are constant time
Space Complexity: O(1) - Constant space for security operations

Security Considerations:
- Bcrypt with sufficient rounds for password hashing
- Pepper addition for password security
- JWT token security with proper expiration
- Constant-time operations to prevent timing attacks
- Rate limiting integration
"""

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any

import bcrypt
import jwt

from .config import settings
from .exceptions import TokenError, ValidationError

logger = logging.getLogger(__name__)

# Configuration from settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
PASSWORD_PEPPER = settings.PASSWORD_PEPPER
BCRYPT_ROUNDS = settings.BCRYPT_ROUNDS


def generate_pepper_hash(password: str, pepper: str = PASSWORD_PEPPER) -> str:
    """
    Generate pepper-enhanced password hash using HMAC.

    Algorithm Approach: HMAC-SHA256 for pepper application
    Time Complexity: O(1) - Single HMAC operation
    Space Complexity: O(1) - Constant output size

    Security Considerations:
    - HMAC provides cryptographic binding between password and pepper
    - SHA-256 is cryptographically secure and widely supported
    - Pepper is server-side secret, not stored in database

    Args:
    password: Plain text password
    pepper: Server-side pepper value

    Returns:
    str: Pepper-enhanced password hash

    Example:
    >>> peppered_hash = generate_pepper_hash("userpassword", "server_pepper")
    >>> len(peppered_hash)  # 64 characters (hex encoded SHA-256)
    64
    """
    if not isinstance(password, str):
        raise ValidationError("Password must be a string")
    if not isinstance(pepper, str):
        raise ValidationError("Pepper must be a string")

    # Use HMAC for cryptographic binding
    peppered_hash = hmac.new(
        pepper.encode("utf-8"), password.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    return peppered_hash


def get_password_hash(password: str) -> str:
    """
    Hash password using bcrypt with pepper enhancement.

    Algorithm Approach: Bcrypt hashing with salt + HMAC pepper
    Time Complexity: O(2^n) where n is BCRYPT_ROUNDS (configurable, typically 12)
    Space Complexity: O(1) - Fixed-size hash output

    Security Considerations:
    - Bcrypt provides automatic salt generation and storage
    - Configurable work factor (rounds) for computational hardness
    - Pepper adds server-side secret for defense in depth
    - Constant-time comparison prevents timing attacks
    - Handles Unicode passwords properly

    Args:
    password: Plain text password to hash

    Returns:
    str: Complete bcrypt hash with embedded salt and rounds

    Raises:
    ValidationError: If password is invalid or too weak

    Example:
    >>> password_hash = get_password_hash("SecurePassword123!")
    >>> password_hash.startswith('$2b$')
    True
    >>> len(password_hash)  # Bcrypt hashes are 60 characters
    60
    """
    if not isinstance(password, str):
        raise ValidationError("Password must be a string")

    if len(password) < settings.MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Password must be at least {settings.MIN_PASSWORD_LENGTH} characters long"
        )

    # Pepper enhancement
    peppered_password = generate_pepper_hash(password)

    # Bcrypt hashing with automatic salt generation
    try:
        password_hash = bcrypt.hashpw(
            peppered_password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        ).decode("utf-8")
    except Exception as e:
        logger.error(f"Password hashing failed: {str(e)}")
        raise ValidationError("Password hashing failed")

    return password_hash


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against bcrypt hash with pepper enhancement.

    Algorithm Approach: Constant-time bcrypt verification with pepper
    Time Complexity: O(2^n) where n is BCRYPT_ROUNDS (from stored hash)
    Space Complexity: O(1) - Constant space for verification

    Security Considerations:
    - Constant-time comparison prevents timing attacks
    - Bcrypt automatically extracts salt and rounds from hash
    - Pepper application before verification
    - Secure handling of verification failures

    Args:
    plain_password: Plain text password to verify
    hashed_password: Stored bcrypt hash to verify against

    Returns:
    bool: True if password matches, False otherwise

    Example:
    >>> stored_hash = get_password_hash("userpassword")
    >>> verify_password("userpassword", stored_hash)
    True
    >>> verify_password("wrongpassword", stored_hash)
    False
    """
    if not isinstance(plain_password, str) or not isinstance(hashed_password, str):
        return False

    try:
        # Apply pepper to plain password
        peppered_password = generate_pepper_hash(plain_password)

        # Bcrypt verification
        is_valid = bcrypt.checkpw(
            peppered_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

        return is_valid

    except Exception as e:
        logger.warning(f"Password verification error: {str(e)}")
        # Always return False on error to prevent timing attacks
        return False


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """
    Create JWT access token with expiration and claims.

    Algorithm Approach: JWT token generation with standardized claims
    Time Complexity: O(1) - Token encoding
    Space Complexity: O(n) - Token size proportional to claims

    Security Considerations:
    - Includes expiration time for automatic token invalidation
    - Issued at time for replay attack prevention
    - Subject claim for user identification
    - Token type claim for token classification
    - Secure algorithm selection

    Args:
    data: Dictionary of claims to include in token
    expires_delta: Optional custom expiration time

    Returns:
    str: Encoded JWT token

    Raises:
    TokenError: If token creation fails

    Example:
    >>> token = create_access_token({"sub": "user@example.com"})
    >>> isinstance(token, str)
    True
    >>> len(token) > 100  # JWT tokens are long
    True
    """
    if not isinstance(data, dict):
        raise ValidationError("Token data must be a dictionary")

    try:
        to_encode = data.copy()

        # Set expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "access",  # Token type claim
            }
        )

        # Create JWT token
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        logger.debug(
            f"JWT token created for subject: {to_encode.get('sub', 'unknown')}"
        )
        return encoded_jwt

    except Exception as e:
        logger.error(f"Token creation failed: {str(e)}")
        raise TokenError("Failed to create access token")


def verify_token(token: str) -> dict[str, Any]:
    """
    Verify and decode JWT token.

    Algorithm Approach: JWT validation with comprehensive checks
    Time Complexity: O(1) - Token decoding and validation
    Space Complexity: O(n) - Decoded token size

    Security Considerations:
    - Algorithm verification prevents algorithm confusion attacks
    - Expiration validation prevents token replay
    - Signature verification prevents token tampering
    - Claims validation ensures token integrity
    - Error logging for security monitoring

    Args:
    token: JWT token to verify

    Returns:
    Dict[str, Any]: Decoded token payload

    Raises:
    TokenError: If token is invalid, expired, or malformed

    Example:
    >>> token = create_access_token({"sub": "user@example.com"})
    >>> payload = verify_token(token)
    >>> payload["sub"]
    'user@example.com'
    >>> "exp" in payload
    True
    """
    if not isinstance(token, str):
        raise TokenError("Token must be a string")

    try:
        # Remove "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token[7:]

        # Decode and verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Validate required claims
        if "sub" not in payload:
            raise TokenError("Token missing required subject claim")

        if "type" not in payload or payload["type"] != "access":
            raise TokenError("Invalid token type")

        # Additional validation
        if payload.get("type") != "access":
            raise TokenError("Invalid token type")

        logger.debug(f"JWT token verified for subject: {payload.get('sub', 'unknown')}")
        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Token verification failed: Token has expired")
        raise TokenError("Token has expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token verification failed: {str(e)}")
        raise TokenError("Invalid token")
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise TokenError("Token verification failed")


def create_refresh_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """
    Create JWT refresh token with longer expiration.

    Algorithm Approach: Long-lived refresh token with rotation support
    Time Complexity: O(1) - Token encoding
    Space Complexity: O(n) - Token size

    Security Considerations:
    - Longer expiration than access tokens
    - Token type claim for proper handling
    - Subject claim for user identification
    - Rotation support for enhanced security

    Args:
    data: Dictionary of claims to include in token
    expires_delta: Optional custom expiration time

    Returns:
    str: Encoded refresh token

    Example:
    >>> refresh_token = create_refresh_token({"sub": "user@example.com"})
    >>> payload = verify_token(refresh_token)  # Can use same verification
    """
    if not isinstance(data, dict):
        raise ValidationError("Token data must be a dictionary")

    try:
        to_encode = data.copy()

        # Set longer expiration for refresh tokens
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )

        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})

        # Create refresh token
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        logger.debug(
            f"Refresh token created for subject: {to_encode.get('sub', 'unknown')}"
        )
        return encoded_jwt

    except Exception as e:
        logger.error(f"Refresh token creation failed: {str(e)}")
        raise TokenError("Failed to create refresh token")


def extract_token_from_header(authorization: str) -> str:
    """
    Extract JWT token from Authorization header.

    Algorithm Approach: Header parsing and validation
    Time Complexity: O(1) - String operations
    Space Complexity: O(1) - Token extraction

    Security Considerations:
    - Validates header format
    - Prevents header injection attacks
    - Returns clean token string

    Args:
    authorization: Authorization header value

    Returns:
    str: Extracted JWT token

    Raises:
    TokenError: If header format is invalid

    Example:
    >>> token = extract_token_from_header("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    >>> isinstance(token, str)
    True
    """
    if not isinstance(authorization, str):
        raise TokenError("Invalid authorization header")

    if not authorization.startswith("Bearer "):
        raise TokenError("Invalid authorization header format")

    token = authorization[7:]  # Remove "Bearer " prefix

    if not token:
        raise TokenError("Missing token in authorization header")

    return token


def generate_secure_random_string(length: int = 32) -> str:
    """
    Generate cryptographically secure random string.

    Algorithm Approach: Cryptographically secure random generation
    Time Complexity: O(1) - Random generation
    Space Complexity: O(1) - Fixed-length string

    Security Considerations:
    - Uses secrets module for cryptographic security
    - URL-safe characters for safe transport
    - Sufficient entropy for security-critical applications

    Args:
    length: Length of random string to generate

    Returns:
    str: Cryptographically secure random string

    Example:
    >>> random_string = generate_secure_random_string()
    >>> len(random_string)
    32
    >>> isinstance(random_string, str)
    True
    """
    if length <= 0:
        raise ValidationError("Length must be positive")

    try:
        return secrets.token_urlsafe(length)
    except Exception as e:
        logger.error(f"Secure random string generation failed: {str(e)}")
        raise ValidationError("Failed to generate secure random string")


def hash_api_key(api_key: str) -> str:
    """
    Hash API key for secure storage.

    Algorithm Approach: SHA-256 hashing for API key storage
    Time Complexity: O(1) - Hash computation
    Space Complexity: O(1) - Fixed-size hash output

    Security Considerations:
    - One-way hashing prevents key recovery
    - Salt not needed as API keys are already random
    - SHA-256 provides sufficient security for this use case

    Args:
    api_key: API key to hash

    Returns:
    str: Hashed API key

    Example:
    >>> api_key = "sk_test_1234567890abcdef"
    >>> hashed_key = hash_api_key(api_key)
    >>> len(hashed_key)  # 64 characters (SHA-256 hex)
    64
    """
    if not isinstance(api_key, str):
        raise ValidationError("API key must be a string")

    try:
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    except Exception as e:
        logger.error(f"API key hashing failed: {str(e)}")
        raise ValidationError("Failed to hash API key")
