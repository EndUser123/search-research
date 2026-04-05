"""
UI Display implementations
"""

from .simple_display import SimpleDisplay
from .tqdm_display import TQDMDisplay

try:
    from .alive_display import AliveDisplay
except ImportError:
    AliveDisplay = None

try:
    from .textual_display import TextualDisplay
except ImportError:
    TextualDisplay = None

try:
    from .rich_display import RichDisplay
except ImportError:
    RichDisplay = None

__all__ = [
    "TQDMDisplay",
    "SimpleDisplay",
    "AliveDisplay",
    "TextualDisplay",
    "RichDisplay",
]
