"""
Goal Templates - Preset goal configurations for quick setup.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

from ..types import GoalType, TrackingType, IntegrationSource


class GoalTemplateCategory(str, Enum):
    """Categories for organizing goal templates"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class GoalTemplate(BaseModel):
    """
    A preset goal configuration that users can quickly create from.
    """
    id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    category: GoalTemplateCategory
    
    # Goal configuration
    goal_type: GoalType
    integration_source: IntegrationSource
    tracking_type: TrackingType
    target_value: int
    unit: str
    visual_variant: Optional[str] = None
    
    # Metadata
    icon: Optional[str] = None
    difficulty: Optional[str] = None  # "beginner", "intermediate", "advanced"
    estimated_time: Optional[str] = None  # e.g., "10 min/day"


class GoalTemplateResponse(BaseModel):
    """Response containing a list of goal templates"""
    templates: List[GoalTemplate]
    count: int


class CreateGoalFromTemplate(BaseModel):
    """Request to create a goal from a template"""
    template_id: str
    name: Optional[str] = None  # Override template name if desired
    target_value: Optional[int] = None  # Override target if desired


# Predefined Goal Templates
GITHUB_TEMPLATES = [
    GoalTemplate(
        id="github_daily_commit",
        name="Daily Commit Streak",
        description="Make at least 1 commit every day to build consistency",
        category=GoalTemplateCategory.DAILY,
        goal_type=GoalType.SHORT_TERM,
        integration_source=IntegrationSource.GITHUB,
        tracking_type=TrackingType.NUMERIC,
        target_value=30,  # 30 days
        unit="days",
        visual_variant="github_streak",
        icon="📅",
        difficulty="beginner",
        estimated_time="10-30 min/day"
    ),
    GoalTemplate(
        id="github_weekly_commits",
        name="Weekly Commit Goal",
        description="Make 10 commits this week",
        category=GoalTemplateCategory.WEEKLY,
        goal_type=GoalType.SHORT_TERM,
        integration_source=IntegrationSource.GITHUB,
        tracking_type=TrackingType.NUMERIC,
        target_value=10,
        unit="commits",
        visual_variant="github_commits",
        icon="💻",
        difficulty="beginner",
        estimated_time="1-2 hours/week"
    ),
    GoalTemplate(
        id="github_daily_pr",
        name="Daily Pull Request",
        description="Create or review 1 PR every day",
        category=GoalTemplateCategory.DAILY,
        goal_type=GoalType.SHORT_TERM,
        integration_source=IntegrationSource.GITHUB,
        tracking_type=TrackingType.NUMERIC,
        target_value=7,  # 7 days
        unit="PRs",
        visual_variant="github_pr",
        icon="🔄",
        difficulty="intermediate",
        estimated_time="30-60 min/day"
    ),
    GoalTemplate(
        id="github_weekly_prs",
        name="Weekly PR Goal",
        description="Create 5 pull requests this week",
        category=GoalTemplateCategory.WEEKLY,
        goal_type=GoalType.SHORT_TERM,
        integration_source=IntegrationSource.GITHUB,
        tracking_type=TrackingType.NUMERIC,
        target_value=5,
        unit="PRs",
        visual_variant="github_pr",
        icon="🎯",
        difficulty="intermediate",
        estimated_time="3-5 hours/week"
    ),
    GoalTemplate(
        id="github_code_review",
        name="Code Review Champion",
        description="Review 5 PRs per week to help your team",
        category=GoalTemplateCategory.WEEKLY,
        goal_type=GoalType.LONG_TERM,
        integration_source=IntegrationSource.GITHUB,
        tracking_type=TrackingType.NUMERIC,
        target_value=20,  # 4 weeks
        unit="reviews",
        visual_variant="github_review",
        icon="👁️",
        difficulty="intermediate",
        estimated_time="2-3 hours/week"
    ),
    GoalTemplate(
        id="github_monthly_commits",
        name="Monthly Commit Goal",
        description="Make 50 commits this month",
        category=GoalTemplateCategory.MONTHLY,
        goal_type=GoalType.LONG_TERM,
        integration_source=IntegrationSource.GITHUB,
        tracking_type=TrackingType.NUMERIC,
        target_value=50,
        unit="commits",
        visual_variant="github_commits",
        icon="🚀",
        difficulty="intermediate",
        estimated_time="10-15 hours/month"
    ),
    GoalTemplate(
        id="github_contributor",
        name="Open Source Contributor",
        description="Contribute to 3 different repositories",
        category=GoalTemplateCategory.MONTHLY,
        goal_type=GoalType.LONG_TERM,
        integration_source=IntegrationSource.GITHUB,
        tracking_type=TrackingType.NUMERIC,
        target_value=3,
        unit="repos",
        visual_variant="github_contrib",
        icon="🌟",
        difficulty="advanced",
        estimated_time="15-20 hours total"
    ),
]

STRAVA_TEMPLATES = [
    GoalTemplate(
        id="strava_daily_run",
        name="Daily Run Streak",
        description="Run every day for 30 days",
        category=GoalTemplateCategory.DAILY,
        goal_type=GoalType.SHORT_TERM,
        integration_source=IntegrationSource.STRAVA,
        tracking_type=TrackingType.NUMERIC,
        target_value=30,
        unit="days",
        visual_variant="strava_streak",
        icon="🏃",
        difficulty="intermediate",
        estimated_time="30-60 min/day"
    ),
    GoalTemplate(
        id="strava_weekly_distance",
        name="Weekly Distance Goal",
        description="Run 20km this week",
        category=GoalTemplateCategory.WEEKLY,
        goal_type=GoalType.SHORT_TERM,
        integration_source=IntegrationSource.STRAVA,
        tracking_type=TrackingType.NUMERIC,
        target_value=20,
        unit="km",
        visual_variant="strava_distance",
        icon="📏",
        difficulty="intermediate",
        estimated_time="3-4 hours/week"
    ),
    GoalTemplate(
        id="strava_monthly_runs",
        name="Monthly Run Count",
        description="Complete 15 runs this month",
        category=GoalTemplateCategory.MONTHLY,
        goal_type=GoalType.LONG_TERM,
        integration_source=IntegrationSource.STRAVA,
        tracking_type=TrackingType.NUMERIC,
        target_value=15,
        unit="runs",
        visual_variant="strava_runs",
        icon="🎽",
        difficulty="beginner",
        estimated_time="0.5-1 hour per run"
    ),
]

MANUAL_TEMPLATES = [
    GoalTemplate(
        id="manual_daily_habit",
        name="Daily Habit Tracker",
        description="Track a daily habit for 21 days",
        category=GoalTemplateCategory.DAILY,
        goal_type=GoalType.SHORT_TERM,
        integration_source=IntegrationSource.MANUAL,
        tracking_type=TrackingType.NUMERIC,
        target_value=21,
        unit="days",
        visual_variant="habit",
        icon="✅",
        difficulty="beginner",
        estimated_time="Varies"
    ),
    GoalTemplate(
        id="manual_project_tasks",
        name="Project Task Completion",
        description="Complete 10 project tasks",
        category=GoalTemplateCategory.CUSTOM,
        goal_type=GoalType.SHORT_TERM,
        integration_source=IntegrationSource.MANUAL,
        tracking_type=TrackingType.NUMERIC,
        target_value=10,
        unit="tasks",
        visual_variant="tasks",
        icon="📋",
        difficulty="beginner",
        estimated_time="Varies"
    ),
]

# Combine all templates
ALL_TEMPLATES = {
    IntegrationSource.GITHUB: GITHUB_TEMPLATES,
    IntegrationSource.STRAVA: STRAVA_TEMPLATES,
    IntegrationSource.MANUAL: MANUAL_TEMPLATES,
}


def get_templates_by_source(source: IntegrationSource) -> List[GoalTemplate]:
    """Get all templates for a specific integration source"""
    return ALL_TEMPLATES.get(source, [])


def get_template_by_id(template_id: str) -> Optional[GoalTemplate]:
    """Get a specific template by its ID"""
    for templates in ALL_TEMPLATES.values():
        for template in templates:
            if template.id == template_id:
                return template
    return None


def get_all_templates() -> List[GoalTemplate]:
    """Get all available templates"""
    all_templates = []
    for templates in ALL_TEMPLATES.values():
        all_templates.extend(templates)
    return all_templates
