"""AI Lane Controller — Milestones 1-5.

Control-plane primitives for a controller Claude session coordinating
up to eight isolated worker lanes: lane identity, durable message
contracts, routing isolation, audit trail, recovery behavior, lane
claiming, live process liveness verification, terminal isolation,
fencing epochs, controller identity, and per-lane scheduling.

Milestone 5: multi-lane controller foundation with eight explicit
lane slots (lane-01 through lane-08), controller command authority,
per-lane serialized handoff queues, and a global UI-input mutex.
"""

from .registry import (
    Lane, load_registry, lane_exists, create_standard_lanes, LANE_IDS,
)
from .messages import (
    create_message,
    validate_message,
    transition_status,
    ALLOWED_SOURCES,
    ALLOWED_DESTINATIONS,
    VALID_STATUSES,
)
from .storage import MessageStorage
from .router import submit_message
from .recovery import list_pending, acknowledge_message, recover_pending
from .controller import (
    ControllerIdentity,
    ControllerCommand,
    ControllerError,
    create_controller_identity,
    validate_controller_command,
)
from .scheduler import Scheduler, UIMutex, LaneQueue, SchedulerError, LANE_STATUSES

__all__ = [
    "Lane", "load_registry", "lane_exists", "create_standard_lanes", "LANE_IDS",
    "create_message", "validate_message", "transition_status",
    "ALLOWED_SOURCES", "ALLOWED_DESTINATIONS", "VALID_STATUSES",
    "MessageStorage",
    "submit_message",
    "list_pending", "acknowledge_message", "recover_pending",
    "ControllerIdentity", "ControllerCommand", "ControllerError",
    "create_controller_identity", "validate_controller_command",
    "Scheduler", "UIMutex", "LaneQueue", "SchedulerError", "LANE_STATUSES",
]