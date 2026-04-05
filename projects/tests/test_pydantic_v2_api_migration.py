"""
Comprehensive test suite for Pydantic V2 API migration validation.

This test suite validates that all API request/response models have been
successfully migrated to Pydantic V2 and work correctly with strict validation,
field validators, and model serialization patterns.

Test Coverage:
- FastAPI Auth API schemas
- Session API request/response models
- Evidence validation API models
- Serialization/deserialization compatibility
- Error handling and validation
- OpenAPI schema generation
- Backward compatibility
"""

import json
from datetime import datetime
from uuid import uuid4

import pytest

# Import the migrated models
try:
    from fastapi_auth_api.src.app.schemas.auth import (
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
except ImportError:
    pytest.skip("FastAPI auth schemas not available", allow_module_level=True)

try:
    from evidence_validation_api.models.schemas import (
        CacheStrategy,
        EvidenceContent,
        EvidenceMetadata,
        EvidenceRequest,
        EvidenceResponse,
        EvidenceType,
        ValidationResult,
        ValidationStatus,
    )
except ImportError:
    pytest.skip("Evidence validation schemas not available", allow_module_level=True)


class TestFastAPIAuthSchemas:
    """Test FastAPI Auth API schemas with Pydantic V2."""

    def test_user_registration_request_valid_data(self):
        """Test UserRegistrationRequest with valid data."""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }

        user = UserRegistrationRequest(**data)
        assert user.email == "test@example.com"
        assert user.password == "SecurePass123!"
        assert user.full_name == "Test User"

        # Test serialization
        json_data = user.model_dump_json()
        parsed_data = json.loads(json_data)
        assert parsed_data["email"] == "test@example.com"

    def test_user_registration_request_password_validation(self):
        """Test password strength validation."""
        # Test weak password
        with pytest.raises(ValueError, match="Password must be at least 8 characters"):
            UserRegistrationRequest(email="test@example.com", password="weak")

        # Test password without uppercase
        with pytest.raises(ValueError, match="uppercase, lowercase, digit, and special character"):
            UserRegistrationRequest(email="test@example.com", password="lowercase123!")

        # Test common patterns
        with pytest.raises(ValueError, match="Password cannot contain common patterns"):
            UserRegistrationRequest(email="test@example.com", password="Password123!")

    def test_user_registration_request_full_name_validation(self):
        """Test full name validation."""
        # Test invalid characters
        with pytest.raises(ValueError, match="Full name contains invalid characters"):
            UserRegistrationRequest(
                email="test@example.com",
                password="SecurePass123!",
                full_name="Test<script>"
            )

    def test_user_login_request_valid_data(self):
        """Test UserLoginRequest with valid data."""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }

        login = UserLoginRequest(**data)
        assert login.email == "test@example.com"
        assert login.password == "SecurePass123!"

    def test_password_change_request_validation(self):
        """Test password change validation with model_validator."""
        data = {
            "current_password": "OldPass123!",
            "new_password": "NewSecurePass123!",
            "confirm_password": "NewSecurePass123!"
        }

        change_req = PasswordChangeRequest(**data)
        assert change_req.new_password == change_req.confirm_password

        # Test mismatched passwords
        with pytest.raises(ValueError, match="Passwords do not match"):
            PasswordChangeRequest(
                current_password="OldPass123!",
                new_password="NewSecurePass123!",
                confirm_password="DifferentPass123!"
            )

    def test_password_reset_request_validation(self):
        """Test password reset validation."""
        data = {
            "token": "reset_token_123",
            "new_password": "NewSecurePass123!",
            "confirm_password": "NewSecurePass123!"
        }

        reset_req = PasswordResetRequest(**data)
        assert reset_req.new_password == reset_req.confirm_password

    def test_user_response_serialization(self):
        """Test UserResponse serialization with datetime fields."""
        now = datetime.now()
        data = {
            "id": 1,
            "email": "test@example.com",
            "is_active": True,
            "is_verified": False,
            "is_admin": False,
            "two_factor_enabled": False,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        user_response = UserResponse(**data)

        # Test model_dump for API responses
        dict_data = user_response.model_dump()
        assert dict_data["email"] == "test@example.com"
        assert "created_at" in dict_data

        # Test JSON serialization
        json_data = user_response.model_dump_json()
        assert isinstance(json_data, str)

    def test_error_response_structure(self):
        """Test ErrorResponse structure and serialization."""
        data = {
            "detail": "Authentication failed",
            "error_code": "AUTH_FAILED",
            "field": "email"
        }

        error = ErrorResponse(**data)
        assert error.detail == "Authentication failed"
        assert error.error_code == "AUTH_FAILED"
        assert error.field == "email"


class TestEvidenceValidationSchemas:
    """Test Evidence Validation API schemas with Pydantic V2."""

    def test_evidence_request_with_content_hash_generation(self):
        """Test EvidenceRequest with automatic content hash generation."""
        content_data = {
            "task_result": "success",
            "execution_time": 120.5
        }

        data = {
            "evidence": {
                "content_type": "application/json",
                "data": content_data
            },
            "metadata": {
                "evidence_type": "task_execution",
                "source_system": "workflow_engine",
                "timestamp": datetime.now().isoformat()
            }
        }

        request = EvidenceRequest(**data)
        assert request.evidence.content_hash is not None
        assert len(request.evidence.content_hash) == 64  # SHA256 hex length

    def test_validation_result_confidence_rounding(self):
        """Test ValidationResult confidence score rounding."""
        data = {
            "is_valid": True,
            "confidence_score": 0.987654321,
            "validation_status": ValidationStatus.VALIDATED
        }

        result = ValidationResult(**data)
        assert result.confidence_score == 0.988  # Rounded to 3 decimal places

    def test_cache_strategy_enum(self):
        """Test CacheStrategy enum validation."""
        assert CacheStrategy.SHORT_TERM == "short_term"
        assert CacheStrategy.MEDIUM_TERM == "medium_term"
        assert CacheStrategy.LONG_TERM == "long_term"
        assert CacheStrategy.NO_CACHE == "no_cache"

    def test_evidence_metadata_uuid_generation(self):
        """Test EvidenceMetadata UUID field handling."""
        data = {
            "evidence_type": EvidenceType.TASK_EXECUTION,
            "source_system": "test_system",
            "timestamp": datetime.now()
        }

        metadata = EvidenceMetadata(**data)
        assert metadata.evidence_id is not None
        assert isinstance(metadata.evidence_id, uuid4().__class__)

    def test_paginated_response_calculations(self):
        """Test PaginatedResponse has_more calculation."""
        data = {
            "items": [{"id": 1}, {"id": 2}],
            "total": 10,
            "offset": 0,
            "limit": 5
        }

        from evidence_validation_api.models.schemas import PaginatedResponse
        response = PaginatedResponse(**data)
        assert response.has_more is True  # (0 + 5) < 10


class TestSerializationCompatibility:
    """Test serialization/deserialization compatibility."""

    def test_json_serialization_roundtrip(self):
        """Test JSON serialization roundtrip compatibility."""
        original_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }

        # Create model
        user = UserRegistrationRequest(**original_data)

        # Serialize to JSON
        json_str = user.model_dump_json()

        # Deserialize from JSON
        parsed_data = json.loads(json_str)
        restored_user = UserRegistrationRequest(**parsed_data)

        assert restored_user.email == original_data["email"]
        assert restored_user.full_name == original_data["full_name"]

    def test_dict_serialization_compatibility(self):
        """Test dict serialization compatibility."""
        user = UserRegistrationRequest(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )

        # Test model_dump
        dict_data = user.model_dump()

        # Should be serializable to JSON
        json_str = json.dumps(dict_data)
        parsed = json.loads(json_str)

        assert parsed["email"] == "test@example.com"

    def test_exclude_unset_fields(self):
        """Test excluding unset fields in serialization."""
        user = UserResponse(
            id=1,
            email="test@example.com",
            is_active=True,
            is_verified=False,
            is_admin=False,
            two_factor_enabled=False
        )

        # Test with exclude_unset
        data = user.model_dump(exclude_unset=True)
        assert "full_name" not in data
        assert "avatar_url" not in data


class TestValidationErrorHandling:
    """Test comprehensive validation error handling."""

    def test_multiple_validation_errors(self):
        """Test multiple validation errors are collected."""
        with pytest.raises(ValueError) as exc_info:
            UserRegistrationRequest(
                email="invalid-email",  # Invalid email
                password="weak",  # Weak password
                full_name=""  # Empty name (might fail validation)
            )

        # Should have validation errors
        assert len(exc_info.value.errors()) > 0

    def test_validation_error_format(self):
        """Test validation error format is consistent."""
        try:
            UserRegistrationRequest(
                email="test@example.com",
                password="weakpass"  # Will fail strength validation
            )
        except ValueError as e:
            # Check that error message is informative
            assert "Password must contain" in str(e)

    def test_nested_model_validation(self):
        """Test nested model validation."""
        with pytest.raises(ValueError):
            # This should fail due to invalid metadata
            EvidenceRequest(
                evidence={
                    "content_type": "application/json",
                    "data": {"test": "data"}
                },
                metadata={}  # Missing required fields
            )


class TestOpenAPICompatibility:
    """Test OpenAPI schema generation compatibility."""

    def test_model_json_schema_generation(self):
        """Test that JSON schemas are generated correctly."""
        schema = UserRegistrationRequest.model_json_schema()

        # Check schema structure
        assert "properties" in schema
        assert "email" in schema["properties"]
        assert "password" in schema["properties"]

        # Check field constraints
        email_prop = schema["properties"]["email"]
        assert "format" in email_prop  # Email format validation

    def test_examples_in_schema(self):
        """Test that examples are included in JSON schema."""
        schema = UserRegistrationRequest.model_json_schema()

        # Check if examples are included
        if "example" in schema.get("json_schema_extra", {}):
            example = schema["json_schema_extra"]["example"]
            assert "email" in example
            assert "password" in example


class TestBackwardCompatibility:
    """Test backward compatibility with API contracts."""

    def test_response_format_compatibility(self):
        """Test that response formats maintain compatibility."""
        # Create a user response
        now = datetime.now()
        user = UserResponse(
            id=1,
            email="test@example.com",
            is_active=True,
            is_verified=False,
            is_admin=False,
            two_factor_enabled=False,
            created_at=now,
            updated_at=now,
        )

        # Serialize as would be sent in API response
        response_data = user.model_dump()

        # Check expected fields exist
        expected_fields = [
            "id", "email", "is_active", "is_verified",
            "is_admin", "two_factor_enabled", "created_at", "updated_at"
        ]

        for field in expected_fields:
            assert field in response_data

    def test_optional_field_handling(self):
        """Test optional fields are handled correctly."""
        # Test with minimal data
        user = UserResponse(
            id=1,
            email="test@example.com",
            is_active=True,
            is_verified=False,
            is_admin=False,
            two_factor_enabled=False
        )

        data = user.model_dump()

        # Optional fields should be None or missing
        assert data.get("full_name") is None
        assert data.get("avatar_url") is None

    def test_datetime_format_compatibility(self):
        """Test datetime format compatibility."""
        now = datetime.now()
        user = UserResponse(
            id=1,
            email="test@example.com",
            is_active=True,
            is_verified=False,
            is_admin=False,
            two_factor_enabled=False,
            created_at=now,
        )

        data = user.model_dump()

        # Datetime should be ISO format
        created_at = data["created_at"]
        assert isinstance(created_at, str)

        # Should be parseable by datetime.fromisoformat
        parsed_datetime = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        assert parsed_datetime.date() == now.date()


@pytest.mark.parametrize("model_class", [
    UserRegistrationRequest,
    UserLoginRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
])
def test_model_instantiation(model_class):
    """Parametrized test for model instantiation with valid data."""
    valid_data_map = {
        UserRegistrationRequest: {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        },
        UserLoginRequest: {
            "email": "test@example.com",
            "password": "SecurePass123!"
        },
        PasswordChangeRequest: {
            "current_password": "OldPass123!",
            "new_password": "NewSecurePass123!",
            "confirm_password": "NewSecurePass123!"
        },
        PasswordResetRequest: {
            "token": "reset_token_123",
            "new_password": "NewSecurePass123!",
            "confirm_password": "NewSecurePass123!"
        }
    }

    data = valid_data_map[model_class]
    instance = model_class(**data)
    assert instance is not None


def test_migration_completeness():
    """Test that all expected models are available and work."""
    # List of models that should be available
    expected_models = [
        UserRegistrationRequest,
        UserLoginRequest,
        TokenResponse,
        UserResponse,
        PasswordChangeRequest,
        ErrorResponse,
    ]

    for model_class in expected_models:
        # Should be importable and instantiable
        assert model_class is not None

        # Should have model_dump method (Pydantic V2)
        assert hasattr(model_class, "model_dump")

        # Should have model_dump_json method (Pydantic V2)
        assert hasattr(model_class, "model_dump_json")

        # Should have model_json_schema method (Pydantic V2)
        assert hasattr(model_class, "model_json_schema")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
