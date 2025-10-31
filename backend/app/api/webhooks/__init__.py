"""
Webhook endpoints for external integrations.

This module contains webhook receivers for various external services.
"""
from . import github, strava

__all__ = ["github", "strava"]
