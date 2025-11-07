"""
Goal-related type definitions and enums.
"""
from enum import Enum


class GoalType(str, Enum):
    """Enum for goal types"""
    LONG_TERM = "long_term"
    SHORT_TERM = "short_term"


class TrackingType(str, Enum):
    """Enum for tracking types"""
    BINARY = "binary"  # Complete or not complete
    NUMERIC = "numeric"  # Track numeric progress


class IntegrationSource(str, Enum):
    """Enum for integration sources"""
    GITHUB = "github"
    STRAVA = "strava"
    MANUAL = "manual"


class GrowthStage(int, Enum):
    """Enum for goal growth stages"""
    BABY = 0
    TEEN = 1
    ADULT = 2
    CROWNED = 3
