"""
Core evidence validation service with intelligent caching.

This module implements the main validation logic with Redis caching,
async processing, and comprehensive error handling.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import redis.asyncio as redis
from sqlalchemy import and_, select

from ..models.database import (
    CacheEntryTable,
    DatabaseManager,
    EvidenceTable,
    ValidationErrorTable,
    ValidationResultTable,
)
from ..models.schemas import (
    CacheStrategy,
    EvidenceRequest,
    EvidenceResponse,
    ValidationResult,
    ValidationStatus,
)

logger = logging.getLogger(__name__)


class EvidenceValidationService:
    """
    Main evidence validation service with caching and async processing.

    This service provides:
    - Real-time evidence validation
    - Intelligent caching with Redis
    - Async processing with callbacks
    - Comprehensive error handling
    - Performance monitoring
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        redis_url: str,
        default_timeout: int = 30,
        max_concurrent_validations: int = 100,
    ):
        """Initialize the validation service.

        Args:
            db_manager: Database manager instance
            redis_url: Redis connection URL
            default_timeout: Default validation timeout in seconds
            max_concurrent_validations: Maximum concurrent validations
        """
        self.db_manager = db_manager
        self.redis_url = redis_url
        self.default_timeout = default_timeout
        self.max_concurrent_validations = max_concurrent_validations

        # Redis client
        self.redis_client: redis.Redis | None = None

        # Active validations tracking
        self.active_validations: dict[UUID, asyncio.Task] = {}
        self.validation_semaphore = asyncio.Semaphore(max_concurrent_validations)

        # Metrics
        self.metrics = {
            "total_validations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "validation_errors": 0,
            "average_processing_time": 0.0,
            "active_count": 0,
        }

    async def initialize(self) -> None:
        """Initialize the validation service."""
        try:
            # Initialize Redis connection
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
            )

            # Test Redis connection
            await self.redis_client.ping()
            logger.info("Evidence validation service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize validation service: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the validation service."""
        try:
            # Cancel active validations
            for task in self.active_validations.values():
                task.cancel()

            # Wait for tasks to complete
            if self.active_validations:
                await asyncio.gather(
                    *self.active_validations.values(), return_exceptions=True
                )

            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()

            logger.info("Evidence validation service shutdown completed")

        except Exception as e:
            logger.error(f"Error during validation service shutdown: {e}")

    async def validate_evidence(self, request: EvidenceRequest) -> EvidenceResponse:
        """
        Validate evidence with caching support.

        Args:
            request: Evidence validation request

        Returns:
            EvidenceResponse with validation results
        """
        start_time = datetime.utcnow()
        request_id = uuid4()

        try:
            # Check cache first
            cached_result = await self._check_cache(request)
            if cached_result:
                self.metrics["cache_hits"] += 1
                logger.info(f"Cache hit for evidence {request.metadata.evidence_id}")

                return EvidenceResponse(
                    request_id=request_id,
                    evidence_id=request.metadata.evidence_id,
                    validation_result=cached_result,
                    processing_time_ms=(datetime.utcnow() - start_time).total_seconds()
                    * 1000,
                    cached_result=True,
                )

            self.metrics["cache_misses"] += 1

            # Perform validation
            if request.async_validation:
                # Async validation
                validation_task = asyncio.create_task(
                    self._validate_evidence_async(request, request_id, start_time)
                )
                self.active_validations[request_id] = validation_task

                # Return immediate response for async validation
                return EvidenceResponse(
                    request_id=request_id,
                    evidence_id=request.metadata.evidence_id,
                    validation_result=ValidationResult(
                        is_valid=False,
                        confidence_score=0.0,
                        validation_status=ValidationStatus.PENDING,
                        validation_rules=[],
                        metadata={"async": True},
                    ),
                    processing_time_ms=(datetime.utcnow() - start_time).total_seconds()
                    * 1000,
                    cached_result=False,
                )
            else:
                # Synchronous validation
                validation_result = await self._validate_evidence_sync(request)

                # Cache the result
                await self._cache_result(request, validation_result)

                # Store in database
                await self._store_validation_result(
                    request_id,
                    request.metadata.evidence_id,
                    validation_result,
                    (datetime.utcnow() - start_time).total_seconds() * 1000,
                )

                return EvidenceResponse(
                    request_id=request_id,
                    evidence_id=request.metadata.evidence_id,
                    validation_result=validation_result,
                    processing_time_ms=(datetime.utcnow() - start_time).total_seconds()
                    * 1000,
                    cached_result=False,
                )

        except Exception as e:
            self.metrics["validation_errors"] += 1
            logger.error(
                f"Validation failed for evidence {request.metadata.evidence_id}: {e}"
            )

            # Store error
            await self._store_validation_error(request, str(e))

            return EvidenceResponse(
                request_id=request_id,
                evidence_id=request.metadata.evidence_id,
                validation_result=ValidationResult(
                    is_valid=False,
                    confidence_score=0.0,
                    validation_status=ValidationStatus.FAILED,
                    validation_rules=[],
                    violations=[f"Validation failed: {str(e)}"],
                    metadata={"error": str(e)},
                ),
                processing_time_ms=(datetime.utcnow() - start_time).total_seconds()
                * 1000,
                cached_result=False,
            )

        finally:
            self.metrics["total_validations"] += 1
            self._update_processing_time_metrics(start_time)

    async def _validate_evidence_sync(
        self, request: EvidenceRequest
    ) -> ValidationResult:
        """Perform synchronous evidence validation."""
        async with self.validation_semaphore:
            try:
                # Extract applicable validation rules
                validation_rules = await self._get_validation_rules(request)

                # Run validations
                violations = []
                warnings = []
                recommendations = []
                total_score = 0.0
                rule_count = len(validation_rules)

                for rule in validation_rules:
                    try:
                        rule_result = await self._apply_validation_rule(request, rule)

                        if not rule_result.get("is_valid", True):
                            violations.extend(rule_result.get("violations", []))

                        warnings.extend(rule_result.get("warnings", []))
                        recommendations.extend(rule_result.get("recommendations", []))
                        total_score += rule_result.get("confidence_score", 0.0)

                    except Exception as e:
                        logger.error(f"Rule {rule.get('rule_id')} failed: {e}")
                        violations.append(
                            f"Rule validation failed: {rule.get('rule_id')}"
                        )

                # Calculate overall confidence score
                confidence_score = total_score / rule_count if rule_count > 0 else 0.0

                # Determine validation status
                if violations:
                    validation_status = ValidationStatus.REJECTED
                    is_valid = False
                elif warnings:
                    validation_status = ValidationStatus.VALIDATED
                    is_valid = True
                else:
                    validation_status = ValidationStatus.VALIDATED
                    is_valid = True

                return ValidationResult(
                    is_valid=is_valid,
                    confidence_score=confidence_score,
                    validation_status=validation_status,
                    validation_rules=[rule.get("rule_id") for rule in validation_rules],
                    violations=violations,
                    warnings=warnings,
                    recommendations=recommendations,
                    metadata={
                        "evidence_type": request.metadata.evidence_type.value,
                        "source_system": request.metadata.source_system,
                        "validation_timestamp": datetime.utcnow().isoformat(),
                    },
                )

            except Exception as e:
                logger.error(f"Synchronous validation failed: {e}")
                return ValidationResult(
                    is_valid=False,
                    confidence_score=0.0,
                    validation_status=ValidationStatus.FAILED,
                    violations=[f"Validation failed: {str(e)}"],
                    metadata={"error": str(e)},
                )

    async def _validate_evidence_async(
        self, request: EvidenceRequest, request_id: UUID, start_time: datetime
    ) -> None:
        """Perform asynchronous evidence validation."""
        try:
            async with self.validation_semaphore:
                # Perform validation
                validation_result = await self._validate_evidence_sync(request)

                # Cache the result
                await self._cache_result(request, validation_result)

                # Store in database
                processing_time_ms = (
                    datetime.utcnow() - start_time
                ).total_seconds() * 1000
                await self._store_validation_result(
                    request_id,
                    request.metadata.evidence_id,
                    validation_result,
                    processing_time_ms,
                )

                # Send webhook notification if provided
                if request.webhook_url:
                    await self._send_webhook_notification(
                        request.webhook_url, request_id, validation_result
                    )

                logger.info(f"Async validation completed for request {request_id}")

        except Exception as e:
            logger.error(f"Async validation failed for request {request_id}: {e}")
            await self._store_validation_error(request, str(e))

        finally:
            # Clean up active validation
            self.active_validations.pop(request_id, None)

    async def _check_cache(
        self, request: EvidenceRequest
    ) -> ValidationResult | None:
        """Check cache for existing validation result."""
        if request.cache_strategy == CacheStrategy.NO_CACHE:
            return None

        try:
            if not self.redis_client:
                return None

            # Generate cache key
            cache_key = self._generate_cache_key(request)

            # Try memory cache first (Redis)
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                # Update hit count
                await self.redis_client.hincrby("cache_stats", cache_key, 1)

                # Parse cached result
                result_dict = json.loads(cached_data)
                return ValidationResult(**result_dict)

            # Check database cache for longer-term storage
            if request.cache_strategy in [
                CacheStrategy.LONG_TERM,
                CacheStrategy.PERSISTENT,
            ]:
                async with self.db_manager.get_session() as session:
                    result = await session.execute(
                        select(CacheEntryTable).where(
                            and_(
                                CacheEntryTable.cache_key == cache_key,
                                CacheEntryTable.expires_at > datetime.utcnow(),
                            )
                        )
                    )
                    cache_entry = result.scalar_one_or_none()

                    if cache_entry:
                        # Update hit count and last accessed
                        cache_entry.hit_count += 1
                        cache_entry.last_accessed = datetime.utcnow()
                        await session.commit()

                        # Store in Redis for faster access
                        await self.redis_client.setex(
                            cache_key,
                            300,  # 5 minutes in Redis
                            json.dumps(cache_entry.validation_result),
                        )

                        return ValidationResult(**cache_entry.validation_result)

        except Exception as e:
            logger.error(f"Cache check failed: {e}")

        return None

    async def _cache_result(
        self, request: EvidenceRequest, result: ValidationResult
    ) -> None:
        """Cache validation result."""
        if request.cache_strategy == CacheStrategy.NO_CACHE:
            return

        try:
            cache_key = self._generate_cache_key(request)
            ttl = self._get_cache_ttl(request.cache_strategy)

            # Cache in Redis
            if self.redis_client and ttl > 0:
                result_dict = result.model_dump()
                await self.redis_client.setex(cache_key, ttl, json.dumps(result_dict))

            # Cache in database for longer-term storage
            if request.cache_strategy in [
                CacheStrategy.LONG_TERM,
                CacheStrategy.PERSISTENT,
            ]:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl)

                async with self.db_manager.get_session() as session:
                    # Check if entry exists
                    existing = await session.execute(
                        select(CacheEntryTable).where(
                            CacheEntryTable.cache_key == cache_key
                        )
                    )
                    cache_entry = existing.scalar_one_or_none()

                    if cache_entry:
                        # Update existing entry
                        cache_entry.validation_result = result.model_dump()
                        cache_entry.expires_at = expires_at
                        cache_entry.last_accessed = datetime.utcnow()
                    else:
                        # Create new entry
                        cache_entry = CacheEntryTable(
                            cache_key=cache_key,
                            evidence_hash=request.evidence.content_hash or "",
                            validation_result=result.model_dump(),
                            expires_at=expires_at,
                            hit_count=1,
                        )
                        session.add(cache_entry)

                    await session.commit()

        except Exception as e:
            logger.error(f"Failed to cache result: {e}")

    def _generate_cache_key(self, request: EvidenceRequest) -> str:
        """Generate cache key for validation request."""
        content = {
            "evidence_type": request.metadata.evidence_type.value,
            "content_hash": request.evidence.content_hash,
            "validation_rules": sorted(request.validation_rules),
            "source_system": request.metadata.source_system,
        }

        content_str = json.dumps(content, sort_keys=True)
        hash_value = hashlib.sha256(content_str.encode()).hexdigest()

        return f"validation:{hash_value}"

    def _get_cache_ttl(self, strategy: CacheStrategy) -> int:
        """Get cache TTL in seconds for strategy."""
        ttl_map = {
            CacheStrategy.SHORT_TERM: 300,  # 5 minutes
            CacheStrategy.MEDIUM_TERM: 3600,  # 1 hour
            CacheStrategy.LONG_TERM: 86400,  # 24 hours
            CacheStrategy.PERSISTENT: 604800,  # 7 days
        }
        return ttl_map.get(strategy, 0)

    async def _get_validation_rules(
        self, request: EvidenceRequest
    ) -> list[dict[str, Any]]:
        """Get applicable validation rules for evidence."""
        # This would typically query the database for applicable rules
        # For now, return basic validation rules
        basic_rules = [
            {
                "rule_id": "content_integrity",
                "name": "Content Integrity Check",
                "description": "Verify evidence content integrity",
                "weight": 1.0,
            },
            {
                "rule_id": "metadata_completeness",
                "name": "Metadata Completeness Check",
                "description": "Verify required metadata is present",
                "weight": 0.8,
            },
            {
                "rule_id": "timestamp_validity",
                "name": "Timestamp Validity Check",
                "description": "Verify timestamps are valid",
                "weight": 0.6,
            },
        ]

        # Filter by requested validation rules if provided
        if request.validation_rules:
            return [
                rule
                for rule in basic_rules
                if rule["rule_id"] in request.validation_rules
            ]

        return basic_rules

    async def _apply_validation_rule(
        self, request: EvidenceRequest, rule: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply a specific validation rule."""
        rule_id = rule["rule_id"]
        violations = []
        warnings = []
        recommendations = []

        try:
            if rule_id == "content_integrity":
                # Check content hash
                if not request.evidence.content_hash:
                    violations.append("Missing content hash")
                elif len(request.evidence.content_hash) != 64:  # SHA-256
                    violations.append("Invalid content hash length")

                # Check content size
                if (
                    request.evidence.size_bytes
                    and request.evidence.size_bytes > 100 * 1024 * 1024
                ):  # 100MB
                    warnings.append("Large evidence content may impact performance")

            elif rule_id == "metadata_completeness":
                # Check required metadata fields
                if not request.metadata.source_system:
                    violations.append("Missing source system")

                if not request.metadata.evidence_type:
                    violations.append("Missing evidence type")

                if not request.metadata.timestamp:
                    violations.append("Missing timestamp")

            elif rule_id == "timestamp_validity":
                # Check timestamp is reasonable (not too far in future/past)
                now = datetime.utcnow()
                if request.metadata.timestamp > now + timedelta(minutes=5):
                    violations.append("Timestamp is too far in the future")

                if request.metadata.timestamp < now - timedelta(days=365):
                    warnings.append("Timestamp is very old")

            return {
                "is_valid": len(violations) == 0,
                "confidence_score": rule.get("weight", 1.0) if not violations else 0.0,
                "violations": violations,
                "warnings": warnings,
                "recommendations": recommendations,
            }

        except Exception as e:
            logger.error(f"Validation rule {rule_id} failed: {e}")
            return {
                "is_valid": False,
                "confidence_score": 0.0,
                "violations": [f"Rule execution failed: {str(e)}"],
                "warnings": [],
                "recommendations": [],
            }

    async def _store_validation_result(
        self,
        request_id: UUID,
        evidence_id: UUID,
        validation_result: ValidationResult,
        processing_time_ms: float,
    ) -> None:
        """Store validation result in database."""
        try:
            async with self.db_manager.get_session() as session:
                # Check if evidence exists
                evidence_result = await session.execute(
                    select(EvidenceTable).where(
                        EvidenceTable.evidence_id == evidence_id
                    )
                )
                evidence = evidence_result.scalar_one_or_none()

                # Create evidence record if it doesn't exist
                if not evidence:
                    # This is a simplified version - in practice, you'd get the full evidence
                    evidence = EvidenceTable(
                        evidence_id=evidence_id,
                        evidence_type="unknown",  # Would be set from request
                        source_system="unknown",
                        timestamp=datetime.utcnow(),
                        content_type="application/json",
                        content_hash="",
                        data={},
                    )
                    session.add(evidence)

                # Create validation result record
                validation_record = ValidationResultTable(
                    result_id=uuid4(),
                    evidence_id=evidence_id,
                    request_id=request_id,
                    is_valid=validation_result.is_valid,
                    validation_status=validation_result.validation_status,
                    confidence_score=validation_result.confidence_score,
                    validator_id=validation_result.validator_id,
                    validation_rules=validation_result.validation_rules,
                    violations=validation_result.violations,
                    warnings=validation_result.warnings,
                    recommendations=validation_result.recommendations,
                    metadata=validation_result.metadata,
                    processing_time_ms=processing_time_ms,
                    cached_result=False,
                    validated_at=validation_result.validated_at,
                )
                session.add(validation_record)

                await session.commit()

        except Exception as e:
            logger.error(f"Failed to store validation result: {e}")

    async def _store_validation_error(
        self, request: EvidenceRequest, error_message: str
    ) -> None:
        """Store validation error in database."""
        try:
            async with self.db_manager.get_session() as session:
                error_record = ValidationErrorTable(
                    error_code="VALIDATION_FAILED",
                    error_message=error_message,
                    error_type="ValidationError",
                    evidence_id=request.metadata.evidence_id,
                    context={
                        "evidence_type": request.metadata.evidence_type.value,
                        "source_system": request.metadata.source_system,
                        "validation_rules": request.validation_rules,
                    },
                )
                session.add(error_record)
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to store validation error: {e}")

    async def _send_webhook_notification(
        self, webhook_url: str, request_id: UUID, result: ValidationResult
    ) -> None:
        """Send webhook notification for async validation completion."""
        try:
            import httpx

            payload = {
                "request_id": str(request_id),
                "validation_result": result.model_dump(),
                "timestamp": datetime.utcnow().isoformat(),
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()

                logger.info(f"Webhook notification sent for request {request_id}")

        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")

    def _update_processing_time_metrics(self, start_time: datetime) -> None:
        """Update processing time metrics."""
        try:
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Update running average
            total_validations = self.metrics["total_validations"]
            current_avg = self.metrics["average_processing_time"]

            new_avg = (
                (current_avg * (total_validations - 1)) + processing_time
            ) / total_validations
            self.metrics["average_processing_time"] = round(new_avg, 2)

        except Exception as e:
            logger.error(f"Failed to update processing time metrics: {e}")

    async def get_validation_status(self, request_id: UUID) -> dict[str, Any] | None:
        """Get status of an ongoing validation."""
        if request_id in self.active_validations:
            task = self.active_validations[request_id]
            return {
                "request_id": request_id,
                "status": "in_progress",
                "task_done": task.done(),
                "task_cancelled": task.cancelled(),
            }

        # Check database for completed validation
        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    select(ValidationResultTable).where(
                        ValidationResultTable.request_id == request_id
                    )
                )
                validation_result = result.scalar_one_or_none()

                if validation_result:
                    return {
                        "request_id": request_id,
                        "status": "completed",
                        "validation_result": {
                            "is_valid": validation_result.is_valid,
                            "validation_status": validation_result.validation_status,
                            "confidence_score": validation_result.confidence_score,
                            "validated_at": validation_result.validated_at.isoformat(),
                        },
                    }

        except Exception as e:
            logger.error(f"Failed to get validation status: {e}")

        return None

    async def get_metrics(self) -> dict[str, Any]:
        """Get validation service metrics."""
        return {
            **self.metrics,
            "active_validations": len(self.active_validations),
            "max_concurrent_validations": self.max_concurrent_validations,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def cancel_validation(self, request_id: UUID) -> bool:
        """Cancel an ongoing validation."""
        if request_id in self.active_validations:
            task = self.active_validations[request_id]
            task.cancel()
            self.active_validations.pop(request_id, None)
            return True
        return False
