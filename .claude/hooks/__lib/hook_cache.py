#!/usr/bin/env python3
from __future__ import annotations

"""Hook Cache Module - Stub implementation"""

import functools
from collections.abc import Callable
from typing import Any


def measure_performance(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)
    return wrapper

__all__ = ["measure_performance"]
