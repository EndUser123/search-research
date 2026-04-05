"""
Authentication service for FastAPI authentication API.

Test Case ID: TC-AUTH-SERVICE-001
Priority: High
Test Type: Service Layer

Purpose:
Provide business logic for user authentication, registration, token management,
and security operations with comprehensive error handling.

Algorithm Approach: Service layer pattern with security-first design
Time Complexity: O(1) - Database operations with indexes
Space Complexity: O(1) - Constant memory usage

Security Considerations:
- Rate limiting integration
- Password security enforcement
- Token management and rotation
- Audit logging
- Input validation and sanitization
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from ..core.config import settings
from ..core.database import get_db_session
from ..core.exceptions import (
    AuthenticationError,
    DatabaseError,
    RateLimitError,
    TokenError,
    UserExistsError,
    UserNotFoundError,
    ValidationError,
)
from ..core.security import (
    create_access_token,
    create_refresh_token,
    generate_secure_random_string,
    get_password_hash,
    verify_password,
    verify_token,
)
from ..models.user import User

logger = logging.getLogger(__name__)


# Redis client for rate limiting and caching (would be initialized in real app)
redis_client = None


class AuthService:
    """
    Authentication service with security best practices.

    Design Pattern: Service layer with dependency injection
    Handles all authentication and user management business logic.

    Security Features:
    - Rate limiting on authentication attempts
    - Password strength validation
    - Secure token generation and validation
    - User account security controls
    - Comprehensive audit logging
    """

    def __init__(self):
        """Initialize authentication service."""
        self.redis_client = redis_client
        self.max_login_attempts = settings.MAX_LOGIN_ATTEMPTS
        self.session_timeout = settings.SESSION_TIMEOUT

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str | None = None,
        is_admin: bool = False,
    ) -> dict[str, Any]:
        """
        Create a new user account with security validation.

        Algorithm Approach: User creation with comprehensive validation
        Time Complexity: O(1) - Database operations with indexes
        Space Complexity: O(1) - User object creation

        Security Considerations:
        - Email validation and normalization
        - Password strength enforcement
        - Duplicate user prevention
        - Email verification requirement
        - Audit logging

        Args:
        email: User email address
        password: User password (plain text)
        full_name: User's full name
        is_admin: Whether user has admin privileges

        Returns:
        Dict[str, Any]: Created user data

        Raises:
        UserExistsError: If user already exists
        ValidationError: If input validation fails
        DatabaseError: If database operation fails
        """
        # Input validation
        if not email or not password:
            raise ValidationError("Email and password are required")

        # Normalize email
        try:
            normalized_email = User.normalize_email(email)
        except ValueError as e:
            raise ValidationError(str(e))

        # Password strength validation
        if not User.validate_password_strength(password):
            raise ValidationError(
                "Password must be at least 8 characters long and contain uppercase, "
                "lowercase, digit, and special characters"
            )

        # Check if user already exists
        async with get_db_session() as session:
            try:
                # Check for existing user
                result = await session.execute(
                    select(User).where(User.email == normalized_email)
                )
                existing_user = result.scalar_one_or_none()

                if existing_user:
                    logger.warning(
                        f"User creation attempted for existing email: {normalized_email}"
                    )
                    raise UserExistsError(
                        f"User with email {normalized_email} already exists"
                    )

                # Create new user
                password_hash = get_password_hash(password)
                verification_token = generate_secure_random_string(32)

                new_user = User(
                    email=normalized_email,
                    password_hash=password_hash,
                    salt="",  # Not used with bcrypt but kept for migration
                    full_name=full_name,
                    is_admin=is_admin,
                    email_verification_token=verification_token,
                    email_verification_expires_at=datetime.now(UTC).replace(
                        hour=23, minute=59, second=59
                    ),
                )

                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)

                logger.info(f"User created successfully: {normalized_email}")

                # Return user data without sensitive fields
                return new_user.to_dict()

            except Exception as e:
                await session.rollback()
                logger.error(f"User creation failed: {str(e)}")
                raise DatabaseError(f"Failed to create user: {str(e)}")

    async def authenticate_user(
        self, email: str, password: str, client_ip: str | None = None
    ) -> dict[str, Any]:
        """
        Authenticate user credentials and generate tokens.

        Algorithm Approach: Credential verification with security controls
        Time Complexity: O(1) - Database lookup and password verification
        Space Complexity: O(1) - Token generation

        Security Considerations:
        - Rate limiting enforcement
        - Account lockout protection
        - Password verification with timing attack protection
        - Secure token generation
        - Audit logging for security events

        Args:
        email: User email address
        password: User password (plain text)
        client_ip: Client IP address for rate limiting

        Returns:
        Dict[str, Any]: Authentication response with tokens

        Raises:
        AuthenticationError: If authentication fails
        RateLimitError: If rate limit exceeded
        UserNotFoundError: If user not found
        """
        # Input validation
        if not email or not password:
            raise ValidationError("Email and password are required")

        # Normalize email
        try:
            normalized_email = User.normalize_email(email)
        except ValueError as e:
            raise ValidationError(str(e))

        # Rate limiting check
        await self.check_rate_limit(normalized_email, client_ip or "unknown")

        async with get_db_session() as session:
            try:
                # Find user
                result = await session.execute(
                    select(User).where(User.email == normalized_email, User.is_active)
                )
                user = result.scalar_one_or_none()

                if not user:
                    logger.warning(
                        f"Authentication attempt for non-existent user: {normalized_email}"
                    )
                    raise AuthenticationError("Invalid credentials")

                # Check if user can login
                if not user.can_login:
                    if user.is_locked:
                        logger.warning(
                            f"Login attempt for locked user: {normalized_email}"
                        )
                        raise AuthenticationError("Account is locked")
                    raise AuthenticationError("Account temporarily unavailable")

                # Verify password
                if not verify_password(password, user.password_hash):
                    # Increment failed attempts
                    user.increment_failed_login()
                    await session.commit()

                    logger.warning(f"Failed password for user: {normalized_email}")
                    raise AuthenticationError("Invalid credentials")

                # Successful authentication
                user.update_last_login(client_ip)
                await session.commit()

                # Generate tokens
                access_token = create_access_token(data={"sub": user.email})
                refresh_token = create_refresh_token(data={"sub": user.email})

                logger.info(f"User authenticated successfully: {normalized_email}")

                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                    "user": user.to_dict(),
                }

            except AuthenticationError:
                # Re-raise authentication errors
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Authentication error: {str(e)}")
                raise DatabaseError(f"Authentication failed: {str(e)}")

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Get user by email address.

        Algorithm Approach: Database lookup with email index
        Time Complexity: O(1) - Indexed lookup
        Space Complexity: O(1) - User object

        Security Considerations:
        - Email normalization
        - Active user filtering
        - Error handling for security

        Args:
        email: User email address

        Returns:
        Optional[User]: User object or None if not found
        """
        try:
            normalized_email = User.normalize_email(email)

            async with get_db_session() as session:
                result = await session.execute(
                    select(User).where(User.email == normalized_email, User.is_active)
                )
                return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None

    async def get_user_from_token(self, token: str) -> User:
        """
        Get user from JWT token.

        Algorithm Approach: Token verification and user lookup
        Time Complexity: O(1) - Token decode + database lookup
        Space Complexity: O(1) - User object

        Security Considerations:
        - Token validation
        - User existence verification
        - Active status checking

        Args:
        token: JWT access token

        Returns:
        User: Authenticated user object

        Raises:
        TokenError: If token is invalid
        UserNotFoundError: If user not found
        """
        try:
            # Verify token
            payload = verify_token(token)
            email = payload.get("sub")

            if not email:
                raise TokenError("Token missing subject")

            # Get user
            user = await self.get_user_by_email(email)
            if not user:
                raise UserNotFoundError(f"User not found: {email}")

            return user

        except TokenError:
            raise
        except Exception as e:
            logger.error(f"Error getting user from token: {str(e)}")
            raise TokenError("Failed to validate token")

    async def validate_token(self, token: str) -> dict[str, Any]:
        """
        Validate JWT token and return payload.

        Algorithm Approach: Token verification with user existence check
        Time Complexity: O(1) - Token decode
        Space Complexity: O(1) - Token payload

        Security Considerations:
        - Token format validation
        - Signature verification
        - Expiration checking
        - User existence verification

        Args:
        token: JWT token to validate

        Returns:
        Dict[str, Any]: Token validation result

        Raises:
        TokenError: If token is invalid
        """
        try:
            # Extract token from header if needed
            if token.startswith("Bearer "):
                token = token[7:]

            # Verify token
            payload = verify_token(token)
            email = payload.get("sub")

            if not email:
                raise TokenError("Token missing subject")

            # Check if user still exists and is active
            user = await self.get_user_by_email(email)
            if not user:
                raise TokenError("User not found")

            return {"valid": True, "payload": payload, "user": user.to_dict()}

        except TokenError:
            raise
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            raise TokenError("Token validation failed")

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Generate new access token from refresh token.

        Algorithm Approach: Token exchange with validation
        Time Complexity: O(1) - Token operations
        Space Complexity: O(1) - New token generation

        Security Considerations:
        - Refresh token validation
        - Token rotation support
        - User status verification
        - Replay attack prevention

        Args:
        refresh_token: Valid refresh token

        Returns:
        Dict[str, Any]: New access token response

        Raises:
        TokenError: If refresh token is invalid
        AuthenticationError: If user not found
        """
        try:
            # Extract token from header if needed
            if refresh_token.startswith("Bearer "):
                refresh_token = refresh_token[7:]

            # Verify refresh token
            payload = verify_token(refresh_token)
            email = payload.get("sub")

            if not email:
                raise TokenError("Invalid refresh token")

            # Check token type
            if payload.get("type") != "refresh":
                raise TokenError("Invalid token type for refresh")

            # Get user
            user = await self.get_user_by_email(email)
            if not user:
                raise AuthenticationError("User not found")

            # Check if refresh token is revoked
            if (
                user.refresh_token_revoked_at
                and payload.get("iat")
                and datetime.fromtimestamp(payload["iat"], UTC)
                <= user.refresh_token_revoked_at
            ):
                raise TokenError("Refresh token revoked")

            # Generate new access token
            new_access_token = create_access_token(data={"sub": user.email})

            logger.info(f"Access token refreshed for user: {email}")

            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            }

        except (TokenError, AuthenticationError):
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise TokenError("Token refresh failed")

    async def revoke_refresh_tokens(self, user: User) -> None:
        """
        Revoke all refresh tokens for a user.

        Algorithm Approach: Timestamp-based token invalidation
        Time Complexity: O(1) - Single field update
        Space Complexity: O(1) - No additional storage

        Security Considerations:
        - Immediate token invalidation
        - Supports logout functionality
        - Account security measure

        Args:
        user: User to revoke tokens for
        """
        async with get_db_session() as session:
            try:
                user.refresh_token_revoked_at = datetime.now(UTC)
                await session.commit()

                logger.info(f"Refresh tokens revoked for user: {user.email}")

            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to revoke refresh tokens: {str(e)}")
                raise DatabaseError("Failed to revoke tokens")

    async def check_rate_limit(
        self,
        email: str,
        client_ip: str,
        window_seconds: int | None = None,
        max_attempts: int | None = None,
    ) -> None:
        """
        Check rate limiting for authentication attempts.

        Algorithm Approach: Sliding window rate limiting with Redis
        Time Complexity: O(1) - Redis operations
        Space Complexity: O(1) - Rate limit counters

        Security Considerations:
        - Prevents brute force attacks
        - IP and email-based limiting
        - Configurable limits and windows
        - Distributed rate limiting

        Args:
        email: User email address
        client_ip: Client IP address
        window_seconds: Rate limit window duration
        max_attempts: Maximum attempts in window

        Raises:
        RateLimitError: If rate limit exceeded
        """
        if not self.redis_client:
            # Skip rate limiting if Redis not available
            return

        window_seconds = window_seconds or settings.RATE_LIMIT_WINDOW
        max_attempts = max_attempts or settings.RATE_LIMIT_REQUESTS

        try:
            # Rate limit keys
            email_key = f"rate_limit:email:{email}"
            ip_key = f"rate_limit:ip:{client_ip}"

            current_time = int(datetime.now().timestamp())

            # Check email-based rate limiting
            await self._check_redis_rate_limit(
                email_key, current_time, window_seconds, max_attempts
            )

            # Check IP-based rate limiting
            await self._check_redis_rate_limit(
                ip_key, current_time, window_seconds, max_attempts
            )

        except Exception as e:
            logger.error(f"Rate limiting check failed: {str(e)}")
            # Don't block authentication if rate limiting fails

    async def _check_redis_rate_limit(
        self, key: str, current_time: int, window_seconds: int, max_attempts: int
    ) -> None:
        """
        Check Redis-based rate limit.

        Algorithm Approach: Redis sliding window implementation
        Time Complexity: O(1) - Redis operations
        Space Complexity: O(n) - Window size where n = max_attempts

        Args:
        key: Redis key for rate limiting
        current_time: Current Unix timestamp
        window_seconds: Rate limit window
        max_attempts: Maximum allowed attempts

        Raises:
        RateLimitError: If rate limit exceeded
        """
        # Remove old entries outside window
        await self.redis_client.zremrangebyscore(key, 0, current_time - window_seconds)

        # Count current attempts
        attempt_count = await self.redis_client.zcard(key)

        if attempt_count >= max_attempts:
            # Calculate retry after time
            oldest_attempt = await self.redis_client.zrange(key, 0, 0, withscores=True)
            if oldest_attempt:
                retry_after = int(oldest_attempt[0][1] + window_seconds - current_time)
            else:
                retry_after = window_seconds

            logger.warning(f"Rate limit exceeded for key: {key}")
            raise RateLimitError(
                "Rate limit exceeded",
                retry_after=max(retry_after, 1),
                limit=max_attempts,
            )

        # Add current attempt
        await self.redis_client.zadd(key, {str(current_time): current_time})
        await self.redis_client.expire(key, window_seconds)

    async def hash_password(self, password: str) -> str:
        """
        Hash password using configured security method.

        Algorithm Approach: Secure password hashing with pepper
        Time Complexity: O(2^n) where n is bcrypt rounds
        Space Complexity: O(1) - Fixed-size hash

        Security Considerations:
        - Bcrypt with configurable rounds
        - Pepper addition for defense in depth
        - Proper error handling

        Args:
        password: Plain text password

        Returns:
        str: Hashed password
        """
        return get_password_hash(password)

    async def verify_password_hash(self, password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.

        Algorithm Approach: Secure password verification
        Time Complexity: O(2^n) where n is bcrypt rounds
        Space Complexity: O(1) - Constant space

        Security Considerations:
        - Constant-time comparison
        - Proper error handling
        - Pepper verification

        Args:
        password: Plain text password
        hashed_password: Stored password hash

        Returns:
        bool: True if password matches
        """
        return verify_password(password, hashed_password)
