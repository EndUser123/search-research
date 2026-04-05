"""Shared library utilities for hooks.

Note: subprocess patching removed from module-level import to prevent
cascading import failures. Use patch_subprocess_context() from
subprocess_patch.py for scoped patching instead.
"""
