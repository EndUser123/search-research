#!/usr/bin/env python3
"""
Evaluation Pipeline and Workflow for the Critic System

This module provides comprehensive evaluation orchestration, workflow management,
and integration capabilities for the Persistent Learning Agent Ecosystem.
"""

import hashlib
import heapq
import json
import logging
import pickle
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

try:
    from .critic import (
        CriticIssue,
        CriticResult,
        CriticSystem,
        CriticType,
        QualityScore,
        Severity,
        create_critic,
    )
except ImportError:
    # Handle relative import for direct execution
    from critic import (
        CriticIssue,
        CriticResult,
        QualityScore,
        Severity,
        create_critic,
    )


class EvaluationStatus(Enum):
    """Status of evaluation processes."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class EvaluationType(Enum):
    """Types of evaluations available."""
    CODE = "code"
    ARCHITECTURE = "architecture"
    PROJECT = "project"
    BATCH = "batch"
    CONTINUOUS = "continuous"


class Priority(Enum):
    """Priority levels for evaluation tasks."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    URGENT = 5


@dataclass
class EvaluationTask:
    """Represents an evaluation task in the pipeline."""
    id: str
    type: EvaluationType
    target: str | Path | dict[str, Any]
    priority: Priority
    status: EvaluationStatus = EvaluationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: CriticResult | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    callback: Callable | None = None
    timeout: float | None = None
    retry_count: int = 0
    max_retries: int = 3
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class EvaluationReport:
    """Comprehensive evaluation report."""
    task_id: str
    evaluation_type: EvaluationType
    target: str
    status: EvaluationStatus
    quality_score: QualityScore | None = None
    issues: list[CriticIssue] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationConfig:
    """Configuration for evaluation pipeline."""
    max_concurrent_evaluations: int = 5
    default_timeout: float = 300.0  # 5 minutes
    cache_enabled: bool = True
    cache_ttl: float = 3600.0  # 1 hour
    retry_enabled: bool = True
    max_retries: int = 3
    continuous_evaluation_interval: float = 60.0  # 1 minute
    auto_save_results: bool = True
    results_directory: Path | None = None
    notification_callbacks: list[Callable] = field(default_factory=list)
    quality_gates: dict[str, float] = field(default_factory=lambda: {
        'critical_threshold': 60.0,
        'warning_threshold': 80.0,
        'max_critical_issues': 5,
        'max_total_issues': 50
    })


class EvaluationCache:
    """Cache for evaluation results to avoid redundant evaluations."""

    def __init__(self, cache_dir: Path, ttl: float = 3600.0):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl
        self._memory_cache = {}
        self._lock = threading.Lock()

    def _get_cache_key(self, target: str | Path | dict[str, Any],
                      evaluation_type: EvaluationType) -> str:
        """Generate cache key for evaluation target."""
        if isinstance(target, (str, Path)):
            # For files, use file path and modification time
            target_path = Path(target)
            if target_path.exists():
                mtime = target_path.stat().st_mtime
                content_hash = f"{target_path}:{mtime}"
            else:
                content_hash = str(target_path)
        else:
            # For other targets, hash the content
            content_hash = hashlib.md5(json.dumps(target, sort_keys=True).encode()).hexdigest()

        return hashlib.sha256(f"{evaluation_type.value}:{content_hash}".encode()).hexdigest()

    def get(self, target: str | Path | dict[str, Any],
           evaluation_type: EvaluationType) -> CriticResult | None:
        """Get cached evaluation result."""
        cache_key = self._get_cache_key(target, evaluation_type)

        with self._lock:
            # Check memory cache first
            if cache_key in self._memory_cache:
                cached_data, timestamp = self._memory_cache[cache_key]
                if time.time() - timestamp < self.ttl:
                    return cached_data
                else:
                    del self._memory_cache[cache_key]

            # Check file cache
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        cached_data, timestamp = pickle.load(f)

                    if time.time() - timestamp < self.ttl:
                        # Store in memory cache
                        self._memory_cache[cache_key] = (cached_data, timestamp)
                        return cached_data
                    else:
                        cache_file.unlink()
                except Exception:
                    cache_file.unlink(missing_ok=True)

        return None

    def set(self, target: str | Path | dict[str, Any],
           evaluation_type: EvaluationType, result: CriticResult):
        """Cache evaluation result."""
        cache_key = self._get_cache_key(target, evaluation_type)
        timestamp = time.time()

        with self._lock:
            # Store in memory cache
            self._memory_cache[cache_key] = (result, timestamp)

            # Store in file cache
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump((result, timestamp), f)
            except Exception as e:
                logging.warning(f"Failed to cache result: {e}")

    def clear(self):
        """Clear all cached results."""
        with self._lock:
            self._memory_cache.clear()
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink(missing_ok=True)


class EvaluationQueue:
    """Priority queue for evaluation tasks."""

    def __init__(self):
        self._tasks: dict[str, EvaluationTask] = {}
        self._priority_queue = []
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)

    def add_task(self, task: EvaluationTask) -> bool:
        """Add task to the queue."""
        with self._condition:
            if task.id in self._tasks:
                return False

            self._tasks[task.id] = task

            # Insert into priority queue (higher priority first)
            heapq.heappush(self._priority_queue, (-task.priority.value, task.created_at.timestamp(), task.id))

            self._condition.notify()
            return True

    def get_next_task(self) -> EvaluationTask | None:
        """Get next task from queue."""
        with self._condition:
            while not self._priority_queue:
                self._condition.wait(timeout=1.0)
                if not self._priority_queue:
                    return None

            _, _, task_id = heapq.heappop(self._priority_queue)
            task = self._tasks.get(task_id)

            if task and task.status == EvaluationStatus.PENDING:
                return task

            return None

    def get_task(self, task_id: str) -> EvaluationTask | None:
        """Get task by ID."""
        with self._lock:
            return self._tasks.get(task_id)

    def update_task_status(self, task_id: str, status: EvaluationStatus,
                          result: CriticResult | None = None,
                          error: str | None = None):
        """Update task status."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.status = status
                if result:
                    task.result = result
                if error:
                    task.error = error
                task.completed_at = datetime.utcnow()

    def get_pending_tasks(self) -> list[EvaluationTask]:
        """Get all pending tasks."""
        with self._lock:
            return [task for task in self._tasks.values() if task.status == EvaluationStatus.PENDING]

    def get_running_tasks(self) -> list[EvaluationTask]:
        """Get all running tasks."""
        with self._lock:
            return [task for task in self._tasks.values() if task.status == EvaluationStatus.RUNNING]

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task.status in [EvaluationStatus.PENDING, EvaluationStatus.RUNNING]:
                task.status = EvaluationStatus.CANCELLED
                task.completed_at = datetime.utcnow()
                return True
            return False

    def clear_completed(self):
        """Clear completed tasks from queue."""
        with self._lock:
            completed_ids = [
                task_id for task_id, task in self._tasks.items()
                if task.status in [EvaluationStatus.COMPLETED, EvaluationStatus.FAILED, EvaluationStatus.CANCELLED]
            ]
            for task_id in completed_ids:
                del self._tasks[task_id]


class EvaluationPipeline:
    """Main evaluation pipeline orchestrating all evaluations."""

    def __init__(self, config: EvaluationConfig | None = None):
        self.config = config or EvaluationConfig()
        self.critic_system = create_critic()
        self.queue = EvaluationQueue()
        self.cache = EvaluationCache(
            cache_dir=self.config.results_directory / "cache" if self.config.results_directory else Path.cwd() / ".evaluation_cache",
            ttl=self.config.cache_ttl
        ) if self.config.cache_enabled else None

        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_evaluations)
        self._running = False
        self._workers = []
        self._continuous_tasks = {}

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Initialize results directory
        if self.config.auto_save_results and self.config.results_directory:
            self.config.results_directory.mkdir(parents=True, exist_ok=True)

    def start(self):
        """Start the evaluation pipeline."""
        if self._running:
            return

        self._running = True

        # Start worker threads
        for i in range(self.config.max_concurrent_evaluations):
            worker = threading.Thread(target=self._worker_loop, name=f"EvaluationWorker-{i}")
            worker.daemon = True
            worker.start()
            self._workers.append(worker)

        # Start continuous evaluation loop
        continuous_worker = threading.Thread(target=self._continuous_evaluation_loop, name="ContinuousEvaluation")
        continuous_worker.daemon = True
        continuous_worker.start()
        self._workers.append(continuous_worker)

        self.logger.info(f"Evaluation pipeline started with {self.config.max_concurrent_evaluations} workers")

    def stop(self):
        """Stop the evaluation pipeline."""
        self._running = False

        # Cancel all running tasks
        running_tasks = self.queue.get_running_tasks()
        for task in running_tasks:
            self.queue.cancel_task(task.id)

        # Wait for workers to finish
        for worker in self._workers:
            worker.join(timeout=5.0)

        self.executor.shutdown(wait=True)
        self.logger.info("Evaluation pipeline stopped")

    def evaluate_code(self, code: str, file_path: str | None = None,
                     priority: Priority = Priority.MEDIUM,
                     metadata: dict[str, Any] | None = None,
                     callback: Callable | None = None) -> str:
        """Submit code evaluation task."""
        task_id = f"code_{int(time.time())}_{hash(code) % 10000}"

        target = {
            'code': code,
            'file_path': file_path
        }

        task = EvaluationTask(
            id=task_id,
            type=EvaluationType.CODE,
            target=target,
            priority=priority,
            metadata=metadata or {},
            callback=callback,
            timeout=self.config.default_timeout
        )

        if self.queue.add_task(task):
            self.logger.debug(f"Code evaluation task submitted: {task_id}")
            return task_id
        else:
            raise RuntimeError(f"Failed to add task: {task_id}")

    def evaluate_file(self, file_path: str | Path,
                     priority: Priority = Priority.MEDIUM,
                     metadata: dict[str, Any] | None = None,
                     callback: Callable | None = None) -> str:
        """Submit file evaluation task."""
        file_path = Path(file_path)
        task_id = f"file_{int(time.time())}_{hash(str(file_path)) % 10000}"

        task = EvaluationTask(
            id=task_id,
            type=EvaluationType.CODE,
            target=file_path,
            priority=priority,
            metadata=metadata or {},
            callback=callback,
            timeout=self.config.default_timeout
        )

        if self.queue.add_task(task):
            self.logger.debug(f"File evaluation task submitted: {task_id}")
            return task_id
        else:
            raise RuntimeError(f"Failed to add task: {task_id}")

    def evaluate_architecture(self, project_path: str | Path,
                            architecture_type: str = "general",
                            priority: Priority = Priority.MEDIUM,
                            metadata: dict[str, Any] | None = None,
                            callback: Callable | None = None) -> str:
        """Submit architecture evaluation task."""
        project_path = Path(project_path)
        task_id = f"arch_{int(time.time())}_{hash(str(project_path)) % 10000}"

        target = {
            'project_path': project_path,
            'architecture_type': architecture_type
        }

        task = EvaluationTask(
            id=task_id,
            type=EvaluationType.ARCHITECTURE,
            target=target,
            priority=priority,
            metadata=metadata or {},
            callback=callback,
            timeout=self.config.default_timeout * 2  # Architecture evaluation takes longer
        )

        if self.queue.add_task(task):
            self.logger.debug(f"Architecture evaluation task submitted: {task_id}")
            return task_id
        else:
            raise RuntimeError(f"Failed to add task: {task_id}")

    def evaluate_project(self, project_path: str | Path,
                        priority: Priority = Priority.MEDIUM,
                        metadata: dict[str, Any] | None = None,
                        callback: Callable | None = None) -> str:
        """Submit comprehensive project evaluation task."""
        project_path = Path(project_path)
        task_id = f"project_{int(time.time())}_{hash(str(project_path)) % 10000}"

        task = EvaluationTask(
            id=task_id,
            type=EvaluationType.PROJECT,
            target=project_path,
            priority=priority,
            metadata=metadata or {},
            callback=callback,
            timeout=self.config.default_timeout * 5  # Project evaluation takes longest
        )

        if self.queue.add_task(task):
            self.logger.debug(f"Project evaluation task submitted: {task_id}")
            return task_id
        else:
            raise RuntimeError(f"Failed to add task: {task_id}")

    def evaluate_batch(self, targets: list[str | Path],
                      evaluation_type: EvaluationType = EvaluationType.CODE,
                      priority: Priority = Priority.MEDIUM,
                      metadata: dict[str, Any] | None = None,
                      callback: Callable | None = None) -> str:
        """Submit batch evaluation task."""
        task_id = f"batch_{int(time.time())}_{hash(str(targets)) % 10000}"

        task = EvaluationTask(
            id=task_id,
            type=EvaluationType.BATCH,
            target={'targets': targets, 'evaluation_type': evaluation_type},
            priority=priority,
            metadata=metadata or {},
            callback=callback,
            timeout=self.config.default_timeout * len(targets)
        )

        if self.queue.add_task(task):
            self.logger.debug(f"Batch evaluation task submitted: {task_id}")
            return task_id
        else:
            raise RuntimeError(f"Failed to add task: {task_id}")

    def add_continuous_evaluation(self, target: str | Path,
                                evaluation_type: EvaluationType,
                                interval: float | None = None,
                                priority: Priority = Priority.LOW,
                                metadata: dict[str, Any] | None = None) -> str:
        """Add continuous evaluation task."""
        task_id = f"continuous_{int(time.time())}_{hash(str(target)) % 10000}"

        self._continuous_tasks[task_id] = {
            'target': target,
            'evaluation_type': evaluation_type,
            'interval': interval or self.config.continuous_evaluation_interval,
            'priority': priority,
            'metadata': metadata or {},
            'last_evaluation': 0.0
        }

        self.logger.debug(f"Continuous evaluation added: {task_id}")
        return task_id

    def remove_continuous_evaluation(self, task_id: str) -> bool:
        """Remove continuous evaluation task."""
        if task_id in self._continuous_tasks:
            del self._continuous_tasks[task_id]
            self.logger.debug(f"Continuous evaluation removed: {task_id}")
            return True
        return False

    def get_task_status(self, task_id: str) -> EvaluationTask | None:
        """Get status of a specific task."""
        return self.queue.get_task(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a specific task."""
        return self.queue.cancel_task(task_id)

    def wait_for_completion(self, task_id: str, timeout: float | None = None) -> CriticResult | None:
        """Wait for task completion and return result."""
        start_time = time.time()

        while True:
            task = self.queue.get_task(task_id)
            if not task:
                return None

            if task.status in [EvaluationStatus.COMPLETED, EvaluationStatus.FAILED, EvaluationStatus.CANCELLED]:
                return task.result

            if timeout and (time.time() - start_time) > timeout:
                self.queue.cancel_task(task_id)
                return None

            time.sleep(0.1)

    def _worker_loop(self):
        """Main worker loop for processing evaluation tasks."""
        while self._running:
            try:
                task = self.queue.get_next_task()
                if not task:
                    continue

                # Update task status to running
                task.status = EvaluationStatus.RUNNING
                task.started_at = datetime.utcnow()

                # Execute evaluation
                future = self.executor.submit(self._execute_task, task)

                # Don't block here - let the executor handle it
                # The result will be processed in a callback

            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                time.sleep(1.0)

    def _execute_task(self, task: EvaluationTask) -> CriticResult:
        """Execute a single evaluation task."""
        try:
            # Check cache first
            if self.cache:
                cached_result = self.cache.get(task.target, task.type)
                if cached_result:
                    self.logger.debug(f"Using cached result for task {task.id}")
                    return cached_result

            # Execute evaluation based on type
            if task.type == EvaluationType.CODE:
                result = self._execute_code_evaluation(task)
            elif task.type == EvaluationType.ARCHITECTURE:
                result = self._execute_architecture_evaluation(task)
            elif task.type == EvaluationType.PROJECT:
                result = self._execute_project_evaluation(task)
            elif task.type == EvaluationType.BATCH:
                result = self._execute_batch_evaluation(task)
            else:
                raise ValueError(f"Unknown evaluation type: {task.type}")

            # Cache result
            if self.cache:
                self.cache.set(task.target, task.type, result)

            # Auto-save result
            if self.config.auto_save_results and self.config.results_directory:
                self._save_result(task, result)

            # Check quality gates
            self._check_quality_gates(task, result)

            # Trigger notifications
            self._trigger_notifications(task, result)

            # Execute callback
            if task.callback:
                try:
                    task.callback(result)
                except Exception as e:
                    self.logger.error(f"Callback error for task {task.id}: {e}")

            return result

        except Exception as e:
            self.logger.error(f"Task execution error for {task.id}: {e}")
            error_result = CriticResult(
                success=False,
                quality_score=QualityScore(
                    overall=0.0,
                    categories={'error': 0.0},
                    issues_by_severity={s.value: 0 for s in Severity},
                    total_issues=0,
                    recommendations=[f"Evaluation failed: {e}"]
                ),
                issues=[],
                recommendations=[f"Evaluation failed: {e}"],
                metrics={'error': str(e)},
                evaluation_time=0.0
            )

            # Execute callback with error
            if task.callback:
                try:
                    task.callback(error_result)
                except Exception:
                    pass

            return error_result

    def _execute_code_evaluation(self, task: EvaluationTask) -> CriticResult:
        """Execute code evaluation."""
        if isinstance(task.target, dict) and 'code' in task.target:
            # Direct code evaluation
            code = task.target['code']
            file_path = task.target.get('file_path')
            return self.critic_system.evaluate_code(code, file_path)
        elif isinstance(task.target, (str, Path)):
            # File evaluation
            file_path = Path(task.target)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            with open(file_path, encoding='utf-8') as f:
                code = f.read()
            return self.critic_system.evaluate_code(code, str(file_path))
        else:
            raise ValueError(f"Invalid target for code evaluation: {task.target}")

    def _execute_architecture_evaluation(self, task: EvaluationTask) -> CriticResult:
        """Execute architecture evaluation."""
        if not isinstance(task.target, dict) or 'project_path' not in task.target:
            raise ValueError("Invalid target for architecture evaluation")

        project_path = Path(task.target['project_path'])
        architecture_type = task.target.get('architecture_type', 'general')

        if not project_path.exists():
            raise FileNotFoundError(f"Project path not found: {project_path}")

        return self.critic_system.evaluate_architecture(project_path, architecture_type)

    def _execute_project_evaluation(self, task: EvaluationTask) -> CriticResult:
        """Execute comprehensive project evaluation."""
        project_path = Path(task.target)

        if not project_path.exists():
            raise FileNotFoundError(f"Project path not found: {project_path}")

        results = self.critic_system.evaluate_project(project_path)

        # Create aggregate result
        if 'aggregate' in results:
            aggregate = results['aggregate']
            quality_score = QualityScore(
                overall=aggregate.get('average_quality_score', 0.0),
                categories={'project': aggregate.get('average_quality_score', 0.0)},
                issues_by_severity=aggregate.get('issues_by_severity', {s.value: 0 for s in Severity}),
                total_issues=aggregate.get('total_issues', 0),
                recommendations=[]
            )

            # Collect all issues and recommendations
            all_issues = []
            all_recommendations = []

            for file_result in results.get('code_files', []):
                all_issues.extend(file_result[1].issues)
                all_recommendations.extend(file_result[1].recommendations)

            if 'architecture' in results:
                all_issues.extend(results['architecture'].issues)
                all_recommendations.extend(results['architecture'].recommendations)

            return CriticResult(
                success=True,
                quality_score=quality_score,
                issues=all_issues,
                recommendations=all_recommendations,
                metrics=aggregate,
                evaluation_time=0.0  # Would need to track this properly
            )
        else:
            raise RuntimeError("Project evaluation failed to produce aggregate results")

    def _execute_batch_evaluation(self, task: EvaluationTask) -> CriticResult:
        """Execute batch evaluation."""
        if not isinstance(task.target, dict) or 'targets' not in task.target:
            raise ValueError("Invalid target for batch evaluation")

        targets = task.target['targets']
        evaluation_type = task.target.get('evaluation_type', EvaluationType.CODE)

        all_issues = []
        all_recommendations = []
        total_quality_score = 0.0
        successful_evaluations = 0

        for target in targets:
            try:
                if evaluation_type == EvaluationType.CODE:
                    result = self._execute_code_evaluation(
                        EvaluationTask(id="temp", type=evaluation_type, target=target, priority=Priority.MEDIUM)
                    )
                else:
                    continue  # Skip unsupported types for now

                all_issues.extend(result.issues)
                all_recommendations.extend(result.recommendations)
                total_quality_score += result.quality_score.overall
                successful_evaluations += 1

            except Exception as e:
                self.logger.error(f"Batch evaluation error for {target}: {e}")
                continue

        avg_quality_score = total_quality_score / max(1, successful_evaluations)

        return CriticResult(
            success=True,
            quality_score=QualityScore(
                overall=avg_quality_score,
                categories={'batch': avg_quality_score},
                issues_by_severity={s.value: sum(1 for issue in all_issues if issue.severity == s) for s in Severity},
                total_issues=len(all_issues),
                recommendations=[]
            ),
            issues=all_issues,
            recommendations=all_recommendations,
            metrics={
                'total_targets': len(targets),
                'successful_evaluations': successful_evaluations,
                'failed_evaluations': len(targets) - successful_evaluations
            },
            evaluation_time=0.0
        )

    def _continuous_evaluation_loop(self):
        """Loop for handling continuous evaluations."""
        while self._running:
            try:
                current_time = time.time()

                for task_id, continuous_task in list(self._continuous_tasks.items()):
                    last_eval = continuous_task['last_evaluation']
                    interval = continuous_task['interval']

                    if current_time - last_eval >= interval:
                        # Submit evaluation task
                        target = continuous_task['target']
                        eval_type = continuous_task['evaluation_type']

                        try:
                            if eval_type == EvaluationType.CODE:
                                task_id_new = self.evaluate_file(
                                    target,
                                    priority=continuous_task['priority'],
                                    metadata=continuous_task['metadata']
                                )
                            elif eval_type == EvaluationType.ARCHITECTURE:
                                task_id_new = self.evaluate_architecture(
                                    target,
                                    priority=continuous_task['priority'],
                                    metadata=continuous_task['metadata']
                                )
                            else:
                                continue

                            continuous_task['last_evaluation'] = current_time
                            self.logger.debug(f"Continuous evaluation submitted: {task_id_new}")

                        except Exception as e:
                            self.logger.error(f"Continuous evaluation error for {task_id}: {e}")
                            continue

                time.sleep(10.0)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Continuous evaluation loop error: {e}")
                time.sleep(10.0)

    def _save_result(self, task: EvaluationTask, result: CriticResult):
        """Save evaluation result to file."""
        if not self.config.results_directory:
            return

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"evaluation_{task.id}_{timestamp}.json"
        output_path = self.config.results_directory / filename

        report = EvaluationReport(
            task_id=task.id,
            evaluation_type=task.type,
            target=str(task.target),
            status=EvaluationStatus.COMPLETED,
            quality_score=result.quality_score,
            issues=result.issues,
            recommendations=result.recommendations,
            metrics=result.metrics,
            execution_time=result.evaluation_time,
            metadata=task.metadata
        )

        try:
            # Convert to serializable format
            serializable_report = {
                'task_id': report.task_id,
                'evaluation_type': report.evaluation_type.value,
                'target': report.target,
                'status': report.status.value,
                'quality_score': {
                    'overall': report.quality_score.overall,
                    'categories': report.quality_score.categories,
                    'total_issues': report.quality_score.total_issues
                },
                'issues': [
                    {
                        'id': issue.id,
                        'type': issue.type.value,
                        'severity': issue.severity.value,
                        'title': issue.title,
                        'description': issue.description,
                        'file_path': issue.file_path,
                        'line_number': issue.line_number,
                        'suggestion': issue.suggestion,
                        'impact': issue.impact,
                        'tags': issue.tags
                    }
                    for issue in report.issues
                ],
                'recommendations': report.recommendations,
                'metrics': report.metrics,
                'execution_time': report.execution_time,
                'timestamp': report.timestamp.isoformat(),
                'metadata': report.metadata
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_report, f, indent=2)

            self.logger.debug(f"Result saved to: {output_path}")

        except Exception as e:
            self.logger.error(f"Failed to save result: {e}")

    def _check_quality_gates(self, task: EvaluationTask, result: CriticResult):
        """Check if quality gates are passed and trigger appropriate actions."""
        if not result.success:
            return

        quality_score = result.quality_score.overall
        critical_issues = len([i for i in result.issues if i.severity == Severity.CRITICAL])
        total_issues = len(result.issues)

        gates = self.config.quality_gates

        # Check critical threshold
        if quality_score < gates['critical_threshold']:
            self.logger.warning(f"Quality gate failed: Score {quality_score:.1f} below threshold {gates['critical_threshold']}")
            # Could trigger additional actions here (e.g., notifications, alerts)

        # Check critical issues count
        if critical_issues > gates['max_critical_issues']:
            self.logger.warning(f"Quality gate failed: {critical_issues} critical issues exceed threshold {gates['max_critical_issues']}")

        # Check total issues count
        if total_issues > gates['max_total_issues']:
            self.logger.warning(f"Quality gate failed: {total_issues} total issues exceed threshold {gates['max_total_issues']}")

    def _trigger_notifications(self, task: EvaluationTask, result: CriticResult):
        """Trigger notification callbacks."""
        for callback in self.config.notification_callbacks:
            try:
                callback(task, result)
            except Exception as e:
                self.logger.error(f"Notification callback error: {e}")

    def get_statistics(self) -> dict[str, Any]:
        """Get pipeline statistics."""
        pending_tasks = self.queue.get_pending_tasks()
        running_tasks = self.queue.get_running_tasks()

        stats = {
            'running': self._running,
            'pending_tasks': len(pending_tasks),
            'running_tasks': len(running_tasks),
            'continuous_tasks': len(self._continuous_tasks),
            'cache_enabled': self.cache is not None,
            'max_workers': self.config.max_concurrent_evaluations
        }

        # Add cache statistics
        if self.cache:
            cache_files = list(self.cache.cache_dir.glob("*.pkl"))
            stats['cache_size'] = len(cache_files)
            stats['cache_memory_size'] = len(self.cache._memory_cache)

        return stats

    def generate_report(self, output_path: Path | None = None) -> str:
        """Generate comprehensive evaluation report."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        report = {
            'report_timestamp': timestamp,
            'pipeline_statistics': self.get_statistics(),
            'configuration': {
                'max_concurrent_evaluations': self.config.max_concurrent_evaluations,
                'default_timeout': self.config.default_timeout,
                'cache_enabled': self.config.cache_enabled,
                'quality_gates': self.config.quality_gates
            },
            'critic_summary': self.critic_system.get_critic_summary()
        }

        report_content = json.dumps(report, indent=2)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            return str(output_path)
        else:
            return report_content


# Factory function for creating evaluation pipelines
def create_evaluation_pipeline(config: EvaluationConfig | None = None) -> EvaluationPipeline:
    """Create a new evaluation pipeline."""
    return EvaluationPipeline(config)


# Convenience functions for quick evaluations
def quick_evaluate_code(code: str, file_path: str | None = None) -> CriticResult:
    """Quick code evaluation without pipeline."""
    critic = create_critic()
    return critic.evaluate_code(code, file_path)


def quick_evaluate_file(file_path: str | Path) -> CriticResult:
    """Quick file evaluation without pipeline."""
    critic = create_critic()
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, encoding='utf-8') as f:
        code = f.read()

    return critic.evaluate_code(code, str(file_path))


def quick_evaluate_project(project_path: str | Path) -> dict[str, Any]:
    """Quick project evaluation without pipeline."""
    critic = create_critic()
    return critic.evaluate_project(Path(project_path))


if __name__ == "__main__":
    # Demo usage
    print("=== Evaluation Pipeline Demo ===")

    # Create evaluation pipeline
    config = EvaluationConfig(
        max_concurrent_evaluations=2,
        cache_enabled=True,
        auto_save_results=True,
        results_directory=Path.cwd() / "evaluation_results"
    )

    pipeline = create_evaluation_pipeline(config)
    pipeline.start()

    try:
        # Submit some evaluation tasks
        sample_code = '''
def test_function():
    """A simple test function."""
    x = 1 + 2
    return x

class TestClass:
    pass
'''

        print("\nSubmitting code evaluation...")
        task_id = pipeline.evaluate_code(sample_code, file_path="test.py")
        print(f"Task submitted: {task_id}")

        # Wait for completion
        print("Waiting for evaluation to complete...")
        result = pipeline.wait_for_completion(task_id, timeout=30.0)

        if result:
            print("Evaluation completed!")
            print(f"Quality Score: {result.quality_score.overall:.1f}")
            print(f"Issues Found: {len(result.issues)}")
            print(f"Execution Time: {result.evaluation_time:.2f}s")
        else:
            print("Evaluation failed or timed out")

        # Show pipeline statistics
        print("\nPipeline Statistics:")
        stats = pipeline.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # Generate report
        print("\nGenerating report...")
        report_path = pipeline.generate_report(Path.cwd() / "evaluation_report.json")
        print(f"Report saved to: {report_path}")

    finally:
        pipeline.stop()
        print("\nPipeline stopped")
