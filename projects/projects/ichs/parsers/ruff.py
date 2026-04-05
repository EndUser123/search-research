from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from .runner import run_command

logger = logging.getLogger(__name__)

# Internal registry mapping check names to callables.
# Callable signature: fn(command: Optional[str] = None, **params) -> Dict[str, Any]
_REGISTRY: dict[str, Callable[..., dict[str, Any]]] = {}


def register(
    name: str,
) -> Callable[[Callable[..., dict[str, Any]]], Callable[..., dict[str, Any]]]:
    """
    Decorator to register a callable check under a given name.

    The callable should return a dict with keys:
      {name, stdout, stderr, returncode, duration_sec}
    """

    def _wrap(func: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
        _REGISTRY[name] = func
        return func

    return _wrap


def available() -> dict[str, Callable[..., dict[str, Any]]]:
    """
    Return a copy of the registered checks mapping.
    """
    return dict(_REGISTRY)


def get(name: str) -> Callable[..., dict[str, Any]] | None:
    """
    Get a registered check by name.
    """
    return _REGISTRY.get(name)


# ------------- Helper runners -------------


def _run_with_default(
    command: str | None, default_cmd: str, **kwargs: Any
) -> dict[str, Any]:
    """
    Run provided command if given; otherwise run a sensible default.

    kwargs are ignored here but accepted to be compatible with CLI param passing.
    """
    cmd = (command or default_cmd).strip()
    if not cmd:
        return {
            "name": default_cmd,
            "stdout": "",
            "stderr": "No command specified.",
            "returncode": 1,
            "duration_sec": 0.0,
        }
    # Delegate to the common runner to ensure schema consistency.
    return run_command(cmd)


# ------------- Built-in checks -------------
# These keep defaults conservative and allow users to override via config.command.
# Each function accepts **params to be forward-compatible with extra arguments.


@register("ruff")
def check_ruff(command: str | None = None, **params: Any) -> dict[str, Any]:
    """
    Run Ruff. Default uses JSON output for robust parsing; users may override.

    Examples:
      - Override in config:
          name: ruff
          command: "ruff check --format text ."
    """
    # Default to JSON format to maximize parser fidelity; CLI parser handles text too.
    default = "ruff check --format json ."
    return _run_with_default(command, default, **params)


@register("mypy")
def check_mypy(command: str | None = None, **params: Any) -> dict[str, Any]:
    """
    Run MyPy with no colors and concise output by default. Parser integration can
    be added similarly to Ruff later.
    """
    default = "mypy --no-color-output --hide-error-context --show-error-codes ."
    return _run_with_default(command, default, **params)


# Optional: generic shell check if users want to invoke arbitrary commands by name
@register("shell")
def check_shell(command: str | None = None, **params: Any) -> dict[str, Any]:
    """
    Run an arbitrary shell command as-is. Intended for ad-hoc checks.
    """
    return _run_with_default(command, command or "", **params)
