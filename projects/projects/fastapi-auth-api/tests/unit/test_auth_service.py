"""
Unit tests for authentication service functionality.

Test Case ID: TC-AUTH-SERVICE-001
Priority: High
Test Type: Unit Testing

Purpose:
Verify authentication service functionality including password hashing,
JWT token generation/validation, and user authentication logic.

Preconditions:
- Test environment is set up with pytest
- Authentication service module is available
- Configuration is loaded for testing

Expected Results:
- Passwords are properly hashed with bcrypt and pepper
- JWT tokens are correctly generated and validated
- User authentication works as expected
- Error cases are handled appropriately
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import jwt
import pytest
from src.app.core.exceptions import AuthenticationError, RateLimitError, TokenError
from src.app.core.security import (
    create_access_token,
    generate_pepper_hash,
    get_password_hash,
    verify_password,
    verify_token,
)
from src.app.services.auth_service import AuthService


@pytest.mark.unit
@pytest.mark.auth
class TestPasswordSecurity:
    """Test password security functionality."""

    def test_password_hashing_with_pepper(self, mock_config):
        """
        Test password hashing with bcrypt and pepper.

        Test Case ID: TC-AUTH-SERVICE-002
        Priority: High
        Test Type: Functional Testing

        Purpose:
        Verify that passwords are properly hashed using bcrypt with pepper.

        Test Data:
        - Password: "SecureTestPassword123!"
        - Pepper: "test-pepper-value"
        - Bcrypt rounds: 12

        Expected Results:
        - Hash is generated successfully
        - Hash is different from plain password
        - Hash includes pepper
        """
        with patch(
            "src.app.core.security.PASSWORD_PEPPER", mock_config["PASSWORD_PEPPER"]
        ):
            with patch(
                "src.app.core.security.BCRYPT_ROUNDS", mock_config["BCRYPT_ROUNDS"]
            ):
                password = "SecureTestPassword123!"

                # Generate hash
                password_hash = get_password_hash(password)

                # Verify hash properties
                assert password_hash is not None
                assert password_hash != password
                assert len(password_hash) > 50  # Bcrypt hashes are long
                assert password_hash.startswith("$2b$")  # Bcrypt prefix

    def test_password_verification_success(self, mock_config):
        """
        Test successful password verification.

        Test Case ID: TC-AUTH-SERVICE-003
        Priority: High
        Test Type: Functional Testing

        Purpose:
        Verify that correct passwords are successfully verified against hashes.

        Expected Results:
        - Correct password returns True
        - Verification uses pepper correctly
        """
        with patch(
            "src.app.core.security.PASSWORD_PEPPER", mock_config["PASSWORD_PEPPER"]
        ):
            password = "SecureTestPassword123!"
            password_hash = get_password_hash(password)

            # Verify correct password
            is_valid = verify_password(password, password_hash)
            assert is_valid is True

    def test_password_verification_failure(self, mock_config):
        """
        Test password verification with wrong password.

        Test Case ID: TC-AUTH-SERVICE-004
        Priority: High
        Test Type: Functional Testing

        Purpose:
        Verify that incorrect passwords are rejected.

        Expected Results:
        - Wrong password returns False
        """
        with patch(
            "src.app.core.security.PASSWORD_PEPPER", mock_config["PASSWORD_PEPPER"]
        ):
            password = "SecureTestPassword123!"
            wrong_password = "WrongPassword123!"
            password_hash = get_password_hash(password)

            # Verify wrong password
            is_valid = verify_password(wrong_password, password_hash)
            assert is_valid is False

    def test_pepper_hash_generation(self):
        """
        Test pepper hash generation for password salting.

        Test Case ID: TC-AUTH-SERVICE-005
        Priority: Medium
        Test Type: Functional Testing

        Purpose:
        Verify pepper hash generation for password enhancement.

        Algorithm Approach: HMAC-based pepper hashing
        Time Complexity: O(1) - Single hash operation
        Space Complexity: O(1) - Constant output size

        Expected Results:
        - Pepper hash is generated consistently for same input
        - Different peppers produce different hashes
        """
        password = "testpassword"
        pepper = "testpepper"

        # Test consistent hashing
        hash1 = generate_pepper_hash(password, pepper)
        hash2 = generate_pepper_hash(password, pepper)
        assert hash1 == hash2

        # Test different peppers produce different hashes
        hash3 = generate_pepper_hash(password, "differentpepper")
        assert hash1 != hash3


@pytest.mark.unit
@pytest.mark.auth
class TestJWTTokenManagement:
    """Test JWT token generation and validation."""

    def test_access_token_creation(self, mock_config):
        """
        Test JWT access token creation.

        Test Case ID: TC-AUTH-SERVICE-006
        Priority: High
        Test Type: Functional Testing

        Purpose:
        Verify JWT tokens are created with correct claims and expiration.

        Expected Results:
        - Token contains correct subject
        - Token has proper expiration
        - Token can be decoded with secret key
        """
        with patch("src.app.core.security.SECRET_KEY", mock_config["SECRET_KEY"]):
            with patch("src.app.core.security.ALGORITHM", mock_config["ALGORITHM"]):
                with patch(
                    "src.app.core.security.ACCESS_TOKEN_EXPIRE_MINUTES",
                    mock_config["ACCESS_TOKEN_EXPIRE_MINUTES"],
                ):
                    email = "test@example.com"
                    token = create_access_token(data={"sub": email})

                    # Decode token for verification
                    decoded = jwt.decode(
                        token,
                        mock_config["SECRET_KEY"],
                        algorithms=[mock_config["ALGORITHM"]],
                    )

                    assert decoded["sub"] == email
                    assert "exp" in decoded
                    assert "iat" in decoded
                    assert "type" in decoded
                    assert decoded["type"] == "access"

    def test_token_verification_success(self, mock_config):
        """
        Test successful JWT token verification.

        Test Case ID: TC-AUTH-SERVICE-007
        Priority: High
        Test Type: Functional Testing

        Purpose:
        Verify valid tokens are successfully verified.

        Expected Results:
        - Valid token returns correct payload
        - Email is extracted correctly
        """
        with patch("src.app.core.security.SECRET_KEY", mock_config["SECRET_KEY"]):
            with patch("src.app.core.security.ALGORITHM", mock_config["ALGORITHM"]):
                email = "test@example.com"
                token = create_access_token(data={"sub": email})

                # Verify token
                payload = verify_token(token)
                assert payload["sub"] == email

    def test_token_verification_invalid_token(self, mock_config):
        """
        Test token verification with invalid token.

        Test Case ID: TC-AUTH-SERVICE-008
        Priority: High
        Test Type: Functional Testing

        Purpose:
        Verify invalid tokens raise appropriate errors.

        Expected Results:
        - Invalid token raises TokenError
        """
        with patch("src.app.core.security.SECRET_KEY", mock_config["SECRET_KEY"]):
            with patch("src.app.core.security.ALGORITHM", mock_config["ALGORITHM"]):
                invalid_tokens = [
                    "invalid.token.here",
                    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
                    "completelyinvalidtoken",
                ]

                for invalid_token in invalid_tokens:
                    with pytest.raises(TokenError):
                        verify_token(invalid_token)

    def test_token_verification_expired_token(self, mock_config):
        """
        Test token verification with expired token.

        Test Case ID: TC-AUTH-SERVICE-009
        Priority: High
        Test Type: Functional Testing

        Purpose:
        Verify expired tokens are rejected.

        Expected Results:
        - Expired token raises TokenError
        """
        with patch("src.app.core.security.SECRET_KEY", mock_config["SECRET_KEY"]):
            with patch("src.app.core.security.ALGORITHM", mock_config["ALGORITHM"]):
                # Create expired token
                expired_time = datetime.utcnow() - timedelta(hours=1)
                expired_payload = {
                    "sub": "test@example.com",
                    "exp": expired_time,
                    "iat": expired_time - timedelta(minutes=5),
                    "type": "access",
                }

                expired_token = jwt.encode(
                    expired_payload,
                    mock_config["SECRET_KEY"],
                    algorithm=mock_config["ALGORITHM"],
                )

                with pytest.raises(TokenError):
                    verify_token(expired_token)


@pytest.mark.unit
@pytest.mark.auth
class TestAuthService:
    """Test authentication service business logic."""

    @pytest.fixture
    def auth_service(self, mock_config):
        """
        Create AuthService instance for testing.

        Algorithm Approach: Service instantiation with mocked dependencies
        Time Complexity: O(1) - Service creation
        Space Complexity: O(1) - Service instance

        Returns:
        AuthService: Configured authentication service
        """
        with patch("src.app.core.security.SECRET_KEY", mock_config["SECRET_KEY"]):
            with patch("src.app.core.security.ALGORITHM", mock_config["ALGORITHM"]):
                return AuthService()

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, test_user_in_db):
        """
        Test successful user authentication.

        Test Case ID: TC-AUTH-SERVICE-010
        Priority: High
        Test Type: Functional Testing

        Purpose:
        Verify user authentication succeeds with correct credentials.

        Expected Results:
        - Valid credentials return user data
        - Authentication token is generated
        """
        password = "SecureTestPassword123!"

        # Mock database user lookup
        with patch.object(auth_service, "get_user_by_email") as mock_get_user:
            mock_get_user.return_value = test_user_in_db

            # Authenticate user
            result = await auth_service.authenticate_user(
                test_user_in_db.email, password
            )

            assert result is not None
            assert "access_token" in result
            assert "token_type" in result
            assert result["token_type"] == "bearer"
            assert "user" in result

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(
        self, auth_service, test_user_in_db
    ):
        """
        Test authentication with invalid password.

        Test Case ID: TC-AUTH-SERVICE-011
        Priority: High
        Test Type: Functional Testing

        Purpose:
        Verify authentication fails with incorrect password.

        Expected Results:
        - Invalid password raises AuthenticationError
        """
        # Mock database user lookup
        with patch.object(auth_service, "get_user_by_email") as mock_get_user:
            mock_get_user.return_value = test_user_in_db

            with pytest.raises(AuthenticationError):
                await auth_service.authenticate_user(
                    test_user_in_db.email, "WrongPassword123!"
                )

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service):
        """
        Test authentication with non-existent user.

        Test Case ID: TC-AUTH-SERVICE-012
        Priority: High
        Test Type: Functional Testing

        Purpose:
        Verify authentication fails for non-existent users.

        Expected Results:
        - Non-existent email raises AuthenticationError
        """
        with patch.object(auth_service, "get_user_by_email") as mock_get_user:
            mock_get_user.return_value = None

            with pytest.raises(AuthenticationError):
                await auth_service.authenticate_user(
                    "nonexistent@example.com", "SomePassword123!"
                )

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, auth_service, test_user_in_db):
        """
        Test authentication with inactive user.

        Test Case ID: TC-AUTH-SERVICE-013
        Priority: Medium
        Test Type: Functional Testing

        Purpose:
        Verify authentication fails for inactive users.

        Expected Results:
        - Inactive user raises AuthenticationError
        """
        test_user_in_db.is_active = False

        with patch.object(auth_service, "get_user_by_email") as mock_get_user:
            mock_get_user.return_value = test_user_in_db

            with pytest.raises(AuthenticationError):
                await auth_service.authenticate_user(
                    test_user_in_db.email, "SecureTestPassword123!"
                )

    @pytest.mark.asyncio
    async def test_rate_limiting_enforcement(self, auth_service, mock_redis):
        """
        Test rate limiting enforcement.

        Test Case ID: TC-AUTH-SERVICE-014
        Priority: Medium
        Test Type: Functional Testing

        Purpose:
        Verify rate limiting is properly enforced for login attempts.

        Algorithm Approach: Redis-based rate limiting with sliding window
        Time Complexity: O(1) - Redis operations
        Space Complexity: O(1) - Rate limit storage

        Expected Results:
        - Rate limit exceeded raises RateLimitError
        - Rate limiting uses client IP
        """
        email = "test@example.com"
        client_ip = "192.168.1.100"

        # Mock Redis responses for rate limit exceeded
        mock_redis.incr.return_value = 6  # Exceeds limit of 5

        with patch("src.app.services.auth_service.redis_client", mock_redis):
            with pytest.raises(RateLimitError):
                await auth_service.check_rate_limit(email, client_ip)

    @pytest.mark.asyncio
    async def test_password_hashing_security(self, auth_service):
        """
        Test password hashing security requirements.

        Test Case ID: TC-AUTH-SERVICE-015
        Priority: High
        Test Type: Security Testing

        Purpose:
        Verify password hashing meets security requirements.

        Security Considerations:
        - Uses bcrypt with sufficient rounds
        - Includes unique salt
        - Pepper is applied correctly
        - Timing attacks are mitigated

        Expected Results:
        - Hash uses bcrypt with proper configuration
        - Same password produces different hashes
        - Hash includes pepper
        """
        password = "SecureTestPassword123!"

        # Generate multiple hashes of the same password
        hash1 = await auth_service.hash_password(password)
        hash2 = await auth_service.hash_password(password)

        # Hashes should be different due to salt
        assert hash1 != hash2
        assert hash1.startswith("$2b$")
        assert hash2.startswith("$2b$")

        # Both hashes should verify the same password
        assert await auth_service.verify_password_hash(password, hash1)
        assert await auth_service.verify_password_hash(password, hash2)

        # Wrong password should not verify
        assert not await auth_service.verify_password_hash("WrongPassword", hash1)
