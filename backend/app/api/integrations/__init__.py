"""
Integration endpoints for OAuth and external service connections.

This module contains OAuth flows and integration setup endpoints.

Integrations:
- github_oauth: Sign in with GitHub (authentication)
- google_oauth: Sign in with Google (authentication)
- github_app: GitHub App installation (activity tracking)
"""
from . import github_oauth, google_oauth, github_app

__all__ = ["github_oauth", "google_oauth", "github_app"]
