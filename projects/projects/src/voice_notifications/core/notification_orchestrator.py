"""
Voice Notification Orchestrator
Manages parallel task execution and coordinates all voice notification components
"""

import asyncio
import logging
import subprocess
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from ..config.config_manager import (
    ConfigManager,
)
from ..filters.intelligent_filter import (
    FilterDecision,
    FilterResult,
    IntelligentNotificationFilter,
    NotificationContext,
)

logger = logging.getLogger(__name__)

class DeliveryStatus(Enum):
    """Voice notification delivery status"""
    PENDING = "pending"
    FILTERED = "filtered"
    QUEUED = "queued"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    FAILED = "failed"
    TIMEOUT = "timeout"

class VoiceEngine(Enum):
    """Available voice engines"""
    PYTTSX3 = "pyttsx3"
    POWERSHELL = "powershell"

@dataclass
class NotificationRequest:
    """Voice notification request"""
    id: str
    notification_type: str
    task_name: str
    session_id: str
    priority: str = "normal"
    timestamp: datetime = field(default_factory=datetime.now)
    tool_name: str | None = None
    context: dict[str, Any] | None = None
    callback: Callable | None = None

@dataclass
class DeliveryResult:
    """Result of voice notification delivery"""
    request_id: str
    status: DeliveryStatus
    engine_used: VoiceEngine | None = None
    delivery_time_ms: float | None = None
    error_message: str | None = None
    filter_result: FilterResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceMetrics:
    """Performance monitoring metrics"""
    total_requests: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    filtered_notifications: int = 0
    average_delivery_time_ms: float = 0.0
    requests_per_minute: float = 0.0
    active_deliveries: int = 0
    queue_size: int = 0
    last_delivery_time: datetime | None = None

class VoiceNotificationOrchestrator:
    """
    Orchestrates voice notification delivery with intelligent filtering,
    parallel execution, and performance monitoring
    """

    def __init__(self, config_path: str | Path | None = None):
        # Initialize configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config

        # Initialize components
        self.intelligent_filter = IntelligentNotificationFilter(self.config)

        # Thread pool for parallel execution
        self.max_workers = self.config.performance.max_concurrent_notifications
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="VoiceNotif")

        # Notification queue and tracking
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        self.active_deliveries: dict[str, asyncio.Task] = {}
        self.delivery_history: list[DeliveryResult] = []
        self.max_history_size = 1000

        # Performance tracking
        self.metrics = PerformanceMetrics()
        self.delivery_times: list[float] = []
        self.request_timestamps: list[datetime] = []
        self._last_cleanup = time.time()

        # Voice engines
        self.pyttsx3_available = self._check_pyttsx3_availability()
        self.powershell_available = self._check_powershell_availability()

        # Background tasks
        self.background_tasks: list[asyncio.Task] = []
        self.running = False

        # Thread safety
        self._lock = threading.RLock()

        logger.info(f"Voice Notification Orchestrator initialized with {self.max_workers} workers")
        logger.info(f"Pyttsx3 available: {self.pyttsx3_available}")
        logger.info(f"PowerShell available: {self.powershell_available}")

    def _check_pyttsx3_availability(self) -> bool:
        """Check if pyttsx3 is available"""
        try:
            import pyttsx3
            # Try to initialize engine
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            engine.stop()
            return True
        except Exception as e:
            logger.warning(f"pyttsx3 not available: {e}")
            return False

    def _check_powershell_availability(self) -> bool:
        """Check if PowerShell speech is available"""
        try:
            # Test PowerShell speech synthesis
            result = subprocess.run([
                "powershell", "-Command",
                "Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.GetInstalledVoices().Count"
            ], capture_output=True, text=True, timeout=10, encoding='utf-8', errors='replace')
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"PowerShell speech not available: {e}")
            return False

    async def start(self) -> None:
        """Start the orchestrator and begin processing notifications"""
        if self.running:
            logger.warning("Orchestrator is already running")
            return

        self.running = True

        # Start background processing task
        self.background_tasks.append(
            asyncio.create_task(self._process_notification_queue(), name="NotificationProcessor")
        )

        # Start performance monitoring task
        if self.config.performance.enable_metrics:
            self.background_tasks.append(
                asyncio.create_task(self._performance_monitor(), name="PerformanceMonitor")
            )

        logger.info("Voice Notification Orchestrator started")

    async def stop(self) -> None:
        """Stop the orchestrator and clean up resources"""
        if not self.running:
            return

        self.running = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Wait for active deliveries to complete or timeout
        if self.active_deliveries:
            logger.info(f"Waiting for {len(self.active_deliveries)} active deliveries to complete")
            await asyncio.gather(*self.active_deliveries.values(), return_exceptions=True)

        # Shutdown executor
        self.executor.shutdown(wait=True)

        # Save behavioral profile
        self.intelligent_filter.save_profile()

        logger.info("Voice Notification Orchestrator stopped")

    async def trigger_notification(
        self,
        notification_type: str,
        task_name: str = "",
        session_id: str = "default",
        priority: str = "normal",
        tool_name: str | None = None,
        context: dict[str, Any] | None = None,
        callback: Callable | None = None
    ) -> DeliveryResult:
        """
        Trigger a voice notification with intelligent filtering and parallel processing
        """
        # Generate unique request ID
        request_id = f"{notification_type}_{int(time.time() * 1000)}_{hash(task_name) % 10000}"

        # Create notification request
        request = NotificationRequest(
            id=request_id,
            notification_type=notification_type,
            task_name=task_name,
            session_id=session_id,
            priority=priority,
            tool_name=tool_name,
            context=context,
            callback=callback
        )

        # Check if notification type is enabled
        if not self.config_manager.is_notification_enabled(notification_type):
            return DeliveryResult(
                request_id=request_id,
                status=DeliveryStatus.FILTERED,
                filter_result=FilterResult(
                    FilterDecision.FILTER_PRIORITY,
                    1.0,
                    f"Notification type '{notification_type}' is disabled"
                )
            )

        # Add to queue for processing
        await self.notification_queue.put(request)

        logger.debug(f"Notification queued: {request_id} ({notification_type})")

        # Return pending result immediately, actual result will be delivered asynchronously
        return DeliveryResult(request_id=request_id, status=DeliveryStatus.PENDING)

    async def _process_notification_queue(self) -> None:
        """Process notifications from the queue"""
        logger.info("Notification queue processor started")

        while self.running:
            try:
                # Get notification from queue with timeout
                request = await asyncio.wait_for(
                    self.notification_queue.get(),
                    timeout=1.0
                )

                # Process notification in background
                task = asyncio.create_task(
                    self._deliver_notification(request),
                    name=f"Delivery-{request.id}"
                )

                self.active_deliveries[request.id] = task

                # Clean up completed tasks
                completed_tasks = [
                    req_id for req_id, task in self.active_deliveries.items()
                    if task.done()
                ]
                for req_id in completed_tasks:
                    del self.active_deliveries[req_id]

            except TimeoutError:
                # Queue was empty, continue
                continue
            except Exception as e:
                logger.error(f"Error in notification queue processor: {e}")

    async def _deliver_notification(self, request: NotificationRequest) -> DeliveryResult:
        """
        Deliver a notification with intelligent filtering and engine selection
        """
        start_time = time.time()

        try:
            # Create notification context
            context = NotificationContext(
                notification_type=request.notification_type,
                task_name=request.task_name,
                session_id=request.session_id,
                timestamp=request.timestamp,
                priority=request.priority,
                tool_name=request.tool_name
            )

            # Apply intelligent filtering
            filter_result = self.intelligent_filter.should_filter_notification(context)
            self.intelligent_filter.record_filter_result(filter_result)

            if filter_result.decision != FilterDecision.ALLOW:
                # Notification was filtered
                result = DeliveryResult(
                    request_id=request.id,
                    status=DeliveryStatus.FILTERED,
                    filter_result=filter_result,
                    delivery_time_ms=(time.time() - start_time) * 1000
                )

                # Call callback if provided
                if request.callback:
                    request.callback(result)

                return result

            # Select voice engine
            engine = self._select_voice_engine(request)

            if not engine:
                # No engine available
                result = DeliveryResult(
                    request_id=request.id,
                    status=DeliveryStatus.FAILED,
                    error_message="No voice engine available",
                    delivery_time_ms=(time.time() - start_time) * 1000
                )

                if request.callback:
                    request.callback(result)

                return result

            # Format message
            message = self._format_message(request)

            # Deliver notification
            delivery_result = await self._deliver_with_engine(engine, message, request)

            # Calculate delivery time
            delivery_time = (time.time() - start_time) * 1000

            # Create final result
            result = DeliveryResult(
                request_id=request.id,
                status=DeliveryStatus.DELIVERED if delivery_result else DeliveryStatus.FAILED,
                engine_used=engine,
                delivery_time_ms=delivery_time,
                error_message=None if delivery_result else "Delivery failed",
                filter_result=filter_result
            )

            # Update metrics
            self._update_delivery_metrics(result)

            # Call callback if provided
            if request.callback:
                request.callback(result)

            return result

        except TimeoutError:
            result = DeliveryResult(
                request_id=request.id,
                status=DeliveryStatus.TIMEOUT,
                delivery_time_ms=(time.time() - start_time) * 1000
            )

            if request.callback:
                request.callback(result)

            return result

        except Exception as e:
            logger.error(f"Error delivering notification {request.id}: {e}")
            result = DeliveryResult(
                request_id=request.id,
                status=DeliveryStatus.FAILED,
                error_message=str(e),
                delivery_time_ms=(time.time() - start_time) * 1000
            )

            if request.callback:
                request.callback(result)

            return result

        finally:
            # Remove from active deliveries
            self.active_deliveries.pop(request.id, None)

    def _select_voice_engine(self, request: NotificationRequest) -> VoiceEngine | None:
        """Select the best voice engine for this notification"""
        # Check configuration preferences
        if self.config.integration.use_pyttsx3_engine and self.pyttsx3_available:
            return VoiceEngine.PYTTSX3

        if self.config.integration.fallback_to_powershell and self.powershell_available:
            return VoiceEngine.POWERSHELL

        # Auto-select based on availability
        if self.pyttsx3_available:
            return VoiceEngine.PYTTSX3

        if self.powershell_available:
            return VoiceEngine.POWERSHELL

        return None

    def _format_message(self, request: NotificationRequest) -> str:
        """Format the notification message"""
        notif_config = self.config_manager.get_notification_config(request.notification_type)

        if notif_config and notif_config.template:
            template = notif_config.template
        else:
            template = f"{request.notification_type}: {{task_name}}"

        # Format with available variables
        try:
            message = template.format(
                task_name=request.task_name or "unknown task",
                session_id=request.session_id,
                tool_name=request.tool_name or "",
                timestamp=request.timestamp.strftime("%H:%M:%S")
            )
        except KeyError as e:
            logger.warning(f"Template formatting error for {request.notification_type}: {e}")
            message = f"{request.notification_type}: {request.task_name}"

        return message

    async def _deliver_with_engine(
        self,
        engine: VoiceEngine,
        message: str,
        request: NotificationRequest
    ) -> bool:
        """Deliver message using specified voice engine"""
        if engine == VoiceEngine.PYTTSX3:
            return await self._deliver_with_pyttsx3(message, request)
        elif engine == VoiceEngine.POWERSHELL:
            return await self._deliver_with_powershell(message, request)
        else:
            raise ValueError(f"Unsupported voice engine: {engine}")

    async def _deliver_with_pyttsx3(self, message: str, request: NotificationRequest) -> bool:
        """Deliver message using pyttsx3"""
        try:
            # Run pyttsx3 in thread pool to avoid blocking
            loop = asyncio.get_event_loop()

            def deliver_sync():
                import pyttsx3

                engine = pyttsx3.init()

                # Configure voice
                voices = engine.getProperty('voices')
                for voice in voices:
                    if self.config.voice.preferred_voice in voice.name:
                        engine.setProperty('voice', voice.id)
                        break
                else:
                    # Fallback to first available voice
                    if voices:
                        engine.setProperty('voice', voices[0].id)

                # Set volume and rate
                engine.setProperty('volume', self.config.voice.volume / 100.0)
                if self.config.voice.rate != -1:
                    engine.setProperty('rate', self.config.voice.rate)

                # Speak
                engine.say(message)
                engine.runAndWait()
                engine.stop()
                return True

            # Execute with timeout
            result = await asyncio.wait_for(
                loop.run_in_executor(self.executor, deliver_sync),
                timeout=30.0  # 30 second timeout
            )

            return result

        except Exception as e:
            logger.error(f"pyttsx3 delivery failed: {e}")
            return False

    async def _deliver_with_powershell(self, message: str, request: NotificationRequest) -> bool:
        """Deliver message using PowerShell speech synthesis"""
        try:
            # Prepare PowerShell command
            voice = self.config.voice.preferred_voice.replace("'", "''")  # Escape single quotes
            volume = self.config.voice.volume
            rate = self.config.voice.rate

            ps_script = f'''
            Add-Type -AssemblyName System.Speech
            $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
            $synth.Volume = {volume}
            $synth.Rate = {rate}

            # Select voice
            $voice = $synth.GetInstalledVoices() | Where-Object {{ $_.VoiceInfo.Name -like "*{voice}*" }} | Select-Object -First 1
            if ($voice) {{
                $synth.SelectVoice($voice.VoiceInfo.Name)
            }}

            $synth.Speak("{message.replace('"', '""')}")
            '''

            # Run PowerShell command
            process = await asyncio.create_subprocess_exec(
                "powershell", "-Command", ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)

            return process.returncode == 0

        except Exception as e:
            logger.error(f"PowerShell delivery failed: {e}")
            return False

    def _update_delivery_metrics(self, result: DeliveryResult) -> None:
        """Update performance metrics"""
        with self._lock:
            self.metrics.total_requests += 1

            if result.status == DeliveryStatus.DELIVERED:
                self.metrics.successful_deliveries += 1
                if result.delivery_time_ms:
                    self.delivery_times.append(result.delivery_time_ms)
                    # Keep only recent delivery times
                    if len(self.delivery_times) > 1000:
                        self.delivery_times = self.delivery_times[-1000:]

                    # Update average
                    self.metrics.average_delivery_time_ms = sum(self.delivery_times) / len(self.delivery_times)

                self.metrics.last_delivery_time = datetime.now()

            elif result.status == DeliveryStatus.FILTERED:
                self.metrics.filtered_notifications += 1

            elif result.status in [DeliveryStatus.FAILED, DeliveryStatus.TIMEOUT]:
                self.metrics.failed_deliveries += 1

            # Update request timestamp for RPS calculation
            self.request_timestamps.append(datetime.now())
            if len(self.request_timestamps) > 3600:  # Keep 1 hour of history
                self.request_timestamps = self.request_timestamps[-3600:]

            # Update queue metrics
            self.metrics.queue_size = self.notification_queue.qsize()
            self.metrics.active_deliveries = len(self.active_deliveries)

            # Store in history
            self.delivery_history.append(result)
            if len(self.delivery_history) > self.max_history_size:
                self.delivery_history = self.delivery_history[-self.max_history_size:]

    async def _performance_monitor(self) -> None:
        """Monitor and log performance metrics"""
        logger.info("Performance monitor started")

        while self.running:
            try:
                await asyncio.sleep(60)  # Monitor every minute

                # Update metrics
                self._update_performance_metrics()

                # Log slow deliveries
                slow_deliveries = [
                    r for r in self.delivery_history[-100:]  # Last 100 deliveries
                    if (r.delivery_time_ms and
                        r.delivery_time_ms > self.config.performance.slow_delivery_threshold_ms)
                ]

                if slow_deliveries and self.config.performance.alert_on_slow_delivery:
                    avg_slow_time = sum(r.delivery_time_ms for r in slow_deliveries) / len(slow_deliveries)
                    logger.warning(
                        f"Detected {len(slow_deliveries)} slow deliveries "
                        f"(avg: {avg_slow_time:.1f}ms)"
                    )

                # Log performance summary
                if self.metrics.total_requests > 0:
                    success_rate = (self.metrics.successful_deliveries / self.metrics.total_requests) * 100
                    logger.info(
                        f"Performance: {self.metrics.total_requests} total, "
                        f"{success_rate:.1f}% success, "
                        f"{self.metrics.average_delivery_time_ms:.1f}ms avg delivery, "
                        f"{self.metrics.requests_per_minute:.1f} req/min"
                    )

            except Exception as e:
                logger.error(f"Error in performance monitor: {e}")

    def _update_performance_metrics(self) -> None:
        """Update calculated performance metrics"""
        with self._lock:
            # Calculate requests per minute
            now = datetime.now()
            one_minute_ago = now - timedelta(minutes=1)
            recent_requests = [
                ts for ts in self.request_timestamps
                if ts >= one_minute_ago
            ]
            self.metrics.requests_per_minute = len(recent_requests)

            # Update other metrics
            self.metrics.queue_size = self.notification_queue.qsize()
            self.metrics.active_deliveries = len(self.active_deliveries)

    def get_metrics(self) -> dict[str, Any]:
        """Get current performance metrics"""
        with self._lock:
            filter_metrics = self.intelligent_filter.get_filter_metrics()

            return {
                "orchestrator": {
                    "total_requests": self.metrics.total_requests,
                    "successful_deliveries": self.metrics.successful_deliveries,
                    "failed_deliveries": self.metrics.failed_deliveries,
                    "filtered_notifications": self.metrics.filtered_notifications,
                    "success_rate_percent": (
                        (self.metrics.successful_deliveries / max(self.metrics.total_requests, 1)) * 100
                    ),
                    "average_delivery_time_ms": self.metrics.average_delivery_time_ms,
                    "requests_per_minute": self.metrics.requests_per_minute,
                    "active_deliveries": self.metrics.active_deliveries,
                    "queue_size": self.metrics.queue_size,
                    "last_delivery_time": self.metrics.last_delivery_time.isoformat() if self.metrics.last_delivery_time else None
                },
                "filter": filter_metrics,
                "engines": {
                    "pyttsx3_available": self.pyttsx3_available,
                    "powershell_available": self.powershell_available
                },
                "configuration": {
                    "max_concurrent_notifications": self.config.performance.max_concurrent_notifications,
                    "target_delivery_ms": self.config.performance.target_delivery_ms,
                    "intelligent_filtering_enabled": self.config.intelligent_filter.enabled
                }
            }

    async def flush_queue(self) -> int:
        """Flush all pending notifications and return count of flushed items"""
        count = 0
        while not self.notification_queue.empty():
            try:
                self.notification_queue.get_nowait()
                count += 1
            except asyncio.QueueEmpty:
                break

        logger.info(f"Flushed {count} pending notifications")
        return count

    def is_running(self) -> bool:
        """Check if the orchestrator is running"""
        return self.running
