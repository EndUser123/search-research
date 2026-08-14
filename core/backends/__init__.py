"""Search backends for local, web, and NotebookLM search."""

from .kg import BACKEND_KG, KGBackend
from .persona import BACKEND_PERSONA, PersonaMemoryBackend
from .rlm import BACKEND_NAME, RLMBackend, SecurityError

__all__ = [
    # KG backend
    "BACKEND_KG",
    "KGBackend",
    # Persona backend
    "BACKEND_PERSONA",
    "PersonaMemoryBackend",
    # RLM backend
    "BACKEND_NAME",
    "RLMBackend",
    "SecurityError",
]
