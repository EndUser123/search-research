"""
FastAPI Authentication API Package

Test Case ID: TC-PACKAGE-001
Priority: Medium
Test Type: Package Configuration

Purpose:
Main package initialization for the FastAPI authentication API.
"""

__version__ = "1.0.0"
__author__ = "FastAPI Auth API Team"
__description__ = (
    "Secure FastAPI Authentication API with JWT and comprehensive security"
)

# Package metadata
__title__ = "FastAPI Authentication API"
__summary__ = "Production-ready authentication API with JWT, rate limiting, and security best practices"

# Import main application for easy access
from .main import app

__all__ = ["app", "__version__"]
