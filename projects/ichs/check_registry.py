from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from .runner import run_command

logger = logging.getLogger(__name__)

# Callable signature: fn(command: Optional[str] = None, **params) -> Dict[str, Any]
CheckFunc = Callable[..., dict[str, Any]]

# Internal registry mapping check names to callables.
_REGISTRY: dict[str, CheckFunc] = {}


def register(name: str) -> Callable[[CheckFunc], CheckFunc]:
    """
    Decorator to register a callable check under a given name.

    The callable should return a dict with keys:
      {name, stdout, stderr, returncode, duration_sec}
    """

    def _wrap(func: CheckFunc) -> CheckFunc:
        if name in _REGISTRY:
            logger.warning("Overwriting existing check registration for '%s'", name)
        _REGISTRY[name] = func
        return func

    return _wrap


def available() -> dict[str, CheckFunc]:
    """Return a copy of the registered checks mapping."""
    return dict(_REGISTRY)


def get(name: str) -> CheckFunc | None:
    """Get a registered check by name."""
    return _REGISTRY.get(name)


def unregister(name: str) -> None:
    """Remove a registered check (useful in tests)."""
    _REGISTRY.pop(name, None)


# ------------- Helper runners -------------


def _run_with_default(
    command: str | None, default_cmd: str, **kwargs: Any
) -> dict[str, Any]:
    """
    Run provided command if given; otherwise run a sensible default.

    Only forwards a safe subset of kwargs to the process runner for compatibility:
      - timeout: float
      - cwd: str
      - env: Dict[str, str]
      - shell: bool
      - encoding: str
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

    allowed = {"timeout", "cwd", "env", "shell", "encoding"}
    forwarded = {k: v for k, v in kwargs.items() if k in allowed}
    # Preserve previous behavior: if caller didn't specify 'shell', let runner default apply.
    try:
        result = run_command(cmd, **forwarded)  # type: ignore[arg-type]
    except TypeError:
        # In case of any mismatch, fall back to safest minimal call.
        logger.debug(
            "run_command signature mismatch; falling back to default invocation for %r",
            cmd,
        )
        result = run_command(cmd)

    return result


# ------------- Built-in checks -------------
# These keep defaults conservative and allow users to override via config.command.
# Each function accepts **params to be forward-compatible with extra arguments.


@register("ruff")
def check_ruff(command: str | None = None, **params: Any) -> dict[str, Any]:
    """
    Run Ruff. Default uses JSON output for robust parsing; users may override.

    Examples (override in config):
      name: ruff
      command: "ruff check --format text ."
    """
    default = "ruff check --format json ."
    return _run_with_default(command, default, **params)


@register("mypy")
def check_mypy(command: str | None = None, **params: Any) -> dict[str, Any]:
    """
    Run MyPy with no colors and concise output by default.
    Parser integration can be added similarly to Ruff later.
    """
    default = "mypy --no-color-output --hide-error-context --show-error-codes ."
    return _run_with_default(command, default, **params)


@register("shell")
def check_shell(command: str | None = None, **params: Any) -> dict[str, Any]:
    """
    Run an arbitrary shell command as-is. Intended for ad-hoc checks.
    """
    # Here, default is whatever the user passed; if nothing passed, return error quickly.
    return _run_with_default(command, command or "", **params)
