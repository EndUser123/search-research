"""Dreaming Cycle (Active Consolidation) - GEMINI EDITION
Implements background knowledge consolidation using Google Gemini 2.0 Flash.
Supports native structured output via Instructor.
"""

import asyncio
import json
import logging
import os
import sqlite3
import time
from enum import Enum
from typing import Any

import psutil

# Pydantic is required for Instructor
from pydantic import BaseModel, Field

# CKS Imports
from ..core.vector_manager import VectorKnowledgeManager

# ML Imports (Provider Agnostic)
try:
    import instructor

    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# Provider Specifics
logger = logging.getLogger(__name__)

# Provider Specifics
try:
    import google.generativeai as genai
    from instructor import from_gemini

    GOOGLE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"❌ Google GenAI Import Failed: {e}")
    GOOGLE_AVAILABLE = False

try:
    from anthropic import AsyncAnthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class ConsolidationMode(str, Enum):
    FULLY_AUTOMATIC = "fully_automatic"
    SEMI_AUTOMATIC = "semi_automatic"
    STRICT_REVIEW = "strict_review"


class RelationHypothesis(BaseModel):
    source_id: str
    target_id: str
    relationship: str = Field(
        ...,
        description="The type of relationship (e.g. 'implements', 'relates_to')",
    )
    reasoning: str = Field(..., description="Why this connection exists")
    confidence: float = Field(..., description="Confidence score 0.0-1.0")


class ResourceGuard:
    """Windows-optimized Resource Guard."""

    def __init__(self, cpu_limit: float = 60.0, mem_limit: float = 80.0) -> None:
        self.cpu_limit = cpu_limit
        self.mem_limit = mem_limit
        self.gaming_processes = [
            "game.exe",
            "steam.exe",
            "discord.exe",
            "zoom.exe",
            "teams.exe",
        ]

    def set_idle_priority(self) -> None:
        """Set process priority to IDLE (Windows friendly)."""
        try:
            p = psutil.Process(os.getpid())
            if os.name == "nt":
                p.nice(psutil.IDLE_PRIORITY_CLASS)
            else:
                p.nice(19)
            logger.info("📉 Process priority set to IDLE.")
        except Exception as e:
            logger.warning(f"Failed to set idle priority: {e}")

    def check_health(self) -> bool:
        """Returns True if system is idle enough to dream."""
        cpu = psutil.cpu_percent(interval=0.5)
        if cpu > self.cpu_limit:
            logger.info(f"⏸️ CPU too high ({cpu}%), skipping.")
            return False

        mem = psutil.virtual_memory()
        if mem.percent > self.mem_limit:
            logger.info(f"⏸️ Memory too high ({mem.percent}%), skipping.")
            return False

        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"].lower() in self.gaming_processes:
                    logger.info(
                        f"🎮 Active process '{proc.info['name']}' detected, skipping.",
                    )
                    return False
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return True


class DreamingService:
    """Orchestrates the consolidation cycle using Google Gemini (Preferred) or Anthropic."""

    def __init__(
        self,
        mode: ConsolidationMode = ConsolidationMode.SEMI_AUTOMATIC,
        db_path: str = "data/knowledge.db",
    ) -> None:
        self.mode = mode
        self.db_path = db_path
        self.resource_guard = ResourceGuard()
        self.vector_manager = VectorKnowledgeManager()

        self._init_db()
        self.client = None
        self.provider = "none"

    def _init_db(self) -> None:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA journal_mode=WAL;")

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_relations (
                    id INTEGER PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relationship TEXT,
                    confidence REAL,
                    reasoning TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at REAL,
                    review_notes TEXT,
                    reviewed_by TEXT,
                    reviewed_at REAL,
                    UNIQUE(source_id, target_id)
                )
            """,
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS graph_edges (
                    id INTEGER PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relationship TEXT,
                    weight REAL DEFAULT 1.0,
                    metadata TEXT,
                    created_at REAL,
                    UNIQUE(source_id, target_id, relationship)
                )
            """,
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.exception(f"Failed to init DB: {e}")

    async def _setup_llm(self) -> bool:
        """Initialize LLM Client (Hybrid Provider Support)."""
        if self.client:
            return True

        # 1. Try Google Gemini (Preferred)
        google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get(
            "GEMINI_API_KEY",
        )

        if google_key and GOOGLE_AVAILABLE:
            try:
                genai.configure(api_key=google_key)
                self.provider = "google"
                logger.info(
                    "✅ DreamingService initialized with Google Gemini Provider (Dynamic Model Selection)",
                )
                return True
            except Exception as e:
                logger.exception(f"Failed to init Google Gemini: {e}")

        # 2. Try Anthropic (Fallback)
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        if anthropic_key and ANTHROPIC_AVAILABLE:
            try:
                self.client = instructor.patch(AsyncAnthropic(api_key=anthropic_key))
                self.provider = "anthropic"
                logger.info("✅ DreamingService initialized with Anthropic Claude")
                return True
            except Exception as e:
                logger.exception(f"Failed to init Anthropic: {e}")

        logger.warning(
            "⚠️ No valid API Key found (checked GOOGLE_API_KEY and ANTHROPIC_API_KEY). Dreaming disabled.",
        )
        return False

    async def get_orphans(self, limit: int = 10) -> list[dict[str, Any]]:
        # Find candidates via Vector Store
        candidates = self.vector_manager.search("", limit=limit * 2)
        orphans = []
        try:
            conn = sqlite3.connect(self.db_path)
            for item in candidates:
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) FROM graph_edges
                    WHERE source_id = ? OR target_id = ?
                """,
                    (item["id"], item["id"]),
                )
                if cursor.fetchone()[0] == 0:
                    orphans.append(item)
                    if len(orphans) >= limit:
                        break
            conn.close()
        except Exception as e:
            logger.exception(f"Orphan detection failed: {e}")
        return orphans

    async def run_cycle(self, max_orphans: int = 5) -> None:
        if not self.resource_guard.check_health():
            return
        self.resource_guard.set_idle_priority()

        if not await self._setup_llm():
            return

        logger.info(f"💤 Dreaming Cycle Started (Provider: {self.provider})...")
        orphans = await self.get_orphans(limit=max_orphans)

        for orphan in orphans:
            semantic_matches = self.vector_manager.search(
                orphan["payload"].get("content", "")[:100],
                limit=5,
            )
            candidates = [
                m["payload"].get("content") for m in semantic_matches if m["id"] != orphan["id"]
            ]
            candidate_ids = [m["id"] for m in semantic_matches if m["id"] != orphan["id"]]

            if not candidates:
                continue

            hypothesis = await self.hypothesize_connections(
                orphan["payload"].get("content"),
                orphan["id"],
                candidates,
                candidate_ids,
            )

            if hypothesis:
                self.validate_and_process(hypothesis)
            await asyncio.sleep(1)

    async def hypothesize_connections(
        self,
        orphan_text: str,
        orphan_id: str,
        candidates: list[str],
        candidate_ids: list[str],
    ) -> RelationHypothesis | None:
        if not self.provider:
            return None

        candidates_context = [
            {"id": cid, "content": txt[:200]}
            for cid, txt in zip(candidate_ids, candidates, strict=False)
        ]

        prompt = f"""
        You are the 'Dreaming' module of a cognitive system.
        Task: connect the 'Orphan' knowledge to one of the 'Candidate' nodes if a strong relationship exists.

        Orphan (ID: {orphan_id}):
        {orphan_text[:500]}...

        Candidates:
        {json.dumps(candidates_context, indent=2)}

        Output a RelationHypothesis.
        - If NO strong connection exists, set confidence < 0.5 and relationship "none".
        """

        try:
            if self.provider == "google":
                # Gemini Native with Failover Strategy (Pro -> Flash -> Lite)
                # Using 'latest' aliases to auto-update as new models release
                models_to_try = [
                    "gemini-1.5-pro-latest",
                    "gemini-1.5-flash-latest",
                    "gemini-1.0-pro-latest",
                ]

                hypothesis = None
                last_error = None

                for model_name in models_to_try:
                    try:
                        logger.info(f"🤔 Dreaming with {model_name}...")

                        # Create Model-Specific Client
                        client = from_gemini(
                            client=genai.GenerativeModel(model_name=model_name),
                            mode=instructor.Mode.GEMINI_JSON,
                        )

                        response = await client.messages.create(
                            messages=[{"role": "user", "content": prompt}],
                            response_model=RelationHypothesis,
                        )
                        hypothesis = response
                        logger.info(f"✨ Success with {model_name}")
                        break  # Success!
                    except Exception as e:
                        logger.warning(f"⚠️ Failed with {model_name}: {e}")
                        last_error = e
                        continue

                if not hypothesis:
                    logger.error(
                        f"❌ All Gemini models failed. Last error: {last_error}",
                    )
                    return None
            else:
                # Anthropic (via Instructor patch)
                hypothesis = await self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                    response_model=RelationHypothesis,
                )

            if hypothesis.target_id not in candidate_ids:
                hypothesis.confidence = 0.0  # Hallucination check

            hypothesis.source_id = orphan_id
            return hypothesis

        except Exception as e:
            logger.exception(f"Hypothesis generation failed: {e}")
            return None

    def validate_and_process(self, hypothesis: RelationHypothesis) -> None:
        if hypothesis.confidence < 0.65:
            self._record_activity(hypothesis, "auto_rejected")
            return

        if hypothesis.confidence >= 0.85:
            if self.mode in [
                ConsolidationMode.FULLY_AUTOMATIC,
                ConsolidationMode.SEMI_AUTOMATIC,
            ]:
                self._commit_to_graph(hypothesis)
            else:
                self._queue_for_review(hypothesis)
        else:
            if self.mode == ConsolidationMode.FULLY_AUTOMATIC:
                self._commit_to_graph(hypothesis)
            else:
                self._queue_for_review(hypothesis)

    def _commit_to_graph(self, hypothesis: RelationHypothesis) -> None:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """
                INSERT OR REPLACE INTO graph_edges
                (source_id, target_id, relationship, weight, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    hypothesis.source_id,
                    hypothesis.target_id,
                    hypothesis.relationship,
                    hypothesis.confidence,
                    json.dumps(
                        {
                            "reason": hypothesis.reasoning,
                            "source": f"dreaming_{self.provider}",
                        },
                    ),
                    time.time(),
                ),
            )
            conn.commit()
            conn.close()
            logger.info(
                f"✅ COMMITTED: {hypothesis.source_id} -> {hypothesis.target_id}",
            )
            self._record_activity(hypothesis, "committed")
        except Exception as e:
            logger.exception(f"Commit failed: {e}")

    def _queue_for_review(self, hypothesis: RelationHypothesis) -> None:
        self._record_activity(hypothesis, "pending")
        logger.info(f"⏳ QUEUED: {hypothesis.source_id} -> {hypothesis.target_id}")

    def _record_activity(self, hypothesis: RelationHypothesis, status: str) -> None:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """
                INSERT OR REPLACE INTO pending_relations
                (source_id, target_id, relationship, confidence, reasoning, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    hypothesis.source_id,
                    hypothesis.target_id,
                    hypothesis.relationship,
                    hypothesis.confidence,
                    hypothesis.reasoning,
                    status,
                    time.time(),
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.exception(f"Audit failed: {e}")
