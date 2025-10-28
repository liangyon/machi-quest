"""
Sample normalized events for testing.

These serve as:
1. Test data for unit tests
2. Reference examples for developers
3. Documentation of the canonical event structure
"""
from datetime import datetime
from uuid import UUID

from app.services.event_normalizer import CanonicalEvent, EventType


# Sample user ID for testing
TEST_USER_ID = UUID("12345678-1234-1234-1234-123456789012")
TEST_PET_ID = UUID("87654321-4321-4321-4321-210987654321")


# GitHub Events
SAMPLE_GITHUB_COMMIT = CanonicalEvent(
    type=EventType.GITHUB_COMMIT,
    timestamp=datetime(2025, 10, 27, 14, 30, 0),
    user_id=TEST_USER_ID,
    value=1.0,
    meta={
        'commit_sha': 'abc123def456',
        'message': 'Add new feature for pet animations',
        'url': 'https://github.com/user/repo/commit/abc123',
        'repository': 'user/machi-quest',
        'branch': 'main',
        'source': 'github',
    }
)

SAMPLE_GITHUB_PR_OPENED = CanonicalEvent(
    type=EventType.GITHUB_PR_OPENED,
    timestamp=datetime(2025, 10, 27, 15, 0, 0),
    user_id=TEST_USER_ID,
    value=1.0,
    meta={
        'pr_number': 42,
        'title': 'Add cool feature',
        'url': 'https://github.com/user/repo/pull/42',
        'repository': 'user/machi-quest',
        'merged': False,
        'action': 'opened',
        'source': 'github',
    }
)

SAMPLE_GITHUB_PR_MERGED = CanonicalEvent(
    type=EventType.GITHUB_PR_MERGED,
    timestamp=datetime(2025, 10, 27, 16, 0, 0),
    user_id=TEST_USER_ID,
    value=1.0,
    meta={
        'pr_number': 42,
        'title': 'Add cool feature',
        'url': 'https://github.com/user/repo/pull/42',
        'repository': 'user/machi-quest',
        'merged': True,
        'action': 'closed',
        'source': 'github',
    }
)

SAMPLE_GITHUB_COMMIT_COMMENT = CanonicalEvent(
    type=EventType.GITHUB_COMMIT_COMMENT,
    timestamp=datetime(2025, 10, 27, 14, 45, 0),
    user_id=TEST_USER_ID,
    value=1.0,
    meta={
        'commit_sha': 'abc123def456',
        'comment_body': 'Great work on this commit!',
        'url': 'https://github.com/user/repo/commit/abc123#comment',
        'repository': 'user/machi-quest',
        'source': 'github',
    }
)


# Fitness & Health (Future integrations - placeholders)
SAMPLE_STRAVA_RUN = CanonicalEvent(
    type=EventType.STRAVA_ACTIVITY,
    timestamp=datetime(2025, 10, 27, 6, 0, 0),
    user_id=TEST_USER_ID,
    value=1.0,
    meta={
        'activity_type': 'run',
        'distance_km': 5.2,
        'duration_minutes': 28,
        'elevation_gain_m': 45,
        'average_pace_per_km': '5:23',
        'source': 'strava',
    }
)

SAMPLE_APPLE_HEALTH_WORKOUT = CanonicalEvent(
    type=EventType.APPLE_HEALTH_WORKOUT,
    timestamp=datetime(2025, 10, 27, 7, 30, 0),
    user_id=TEST_USER_ID,
    value=1.0,
    meta={
        'workout_type': 'yoga',
        'duration_minutes': 45,
        'calories_burned': 180,
        'source': 'apple_health',
    }
)

SAMPLE_APPLE_HEALTH_STEPS = CanonicalEvent(
    type=EventType.APPLE_HEALTH_STEPS,
    timestamp=datetime(2025, 10, 27, 23, 59, 0),
    user_id=TEST_USER_ID,
    value=1.0,
    meta={
        'step_count': 10543,
        'goal_reached': True,
        'source': 'apple_health',
    }
)


# Manual Events
SAMPLE_MANUAL_HABIT = CanonicalEvent(
    type=EventType.MANUAL_HABIT,
    timestamp=datetime(2025, 10, 27, 20, 0, 0),
    user_id=TEST_USER_ID,
    value=1.0,
    meta={
        'title': 'Practiced guitar for 30 minutes',
        'category': 'music',
        'duration_minutes': 30,
        'source': 'manual',
    }
)

SAMPLE_MANUAL_GOAL_PROGRESS = CanonicalEvent(
    type=EventType.MANUAL_GOAL_PROGRESS,
    timestamp=datetime(2025, 10, 27, 21, 0, 0),
    user_id=TEST_USER_ID,
    value=50.0,  # 50 pages read
    meta={
        'title': 'Read 50 pages of "The Great Gatsby"',
        'category': 'reading',
        'quantity': 50,
        'unit': 'pages',
        'source': 'manual',
    }
)


# Future integrations (placeholders)
SAMPLE_DUOLINGO_LESSON = CanonicalEvent(
    type=EventType.DUOLINGO_LESSON,
    timestamp=datetime(2025, 10, 27, 19, 0, 0),
    user_id=TEST_USER_ID,
    value=1.0,
    meta={
        'language': 'Spanish',
        'lesson_name': 'Greetings & Basics',
        'xp_earned': 20,
        'streak_days': 45,
        'source': 'duolingo',
    }
)

SAMPLE_GOODREADS_BOOK = CanonicalEvent(
    type=EventType.GOODREADS_BOOK,
    timestamp=datetime(2025, 10, 27, 22, 0, 0),
    user_id=TEST_USER_ID,
    value=1.0,
    meta={
        'book_title': 'The Great Gatsby',
        'author': 'F. Scott Fitzgerald',
        'status': 'finished',
        'rating': 5,
        'source': 'goodreads',
    }
)


# List of all samples for easy iteration in tests
ALL_SAMPLE_EVENTS = [
    SAMPLE_GITHUB_COMMIT,
    SAMPLE_GITHUB_PR_OPENED,
    SAMPLE_GITHUB_PR_MERGED,
    SAMPLE_GITHUB_COMMIT_COMMENT,
    SAMPLE_STRAVA_RUN,
    SAMPLE_APPLE_HEALTH_WORKOUT,
    SAMPLE_APPLE_HEALTH_STEPS,
    SAMPLE_MANUAL_HABIT,
    SAMPLE_MANUAL_GOAL_PROGRESS,
    SAMPLE_DUOLINGO_LESSON,
    SAMPLE_GOODREADS_BOOK,
]

# Group by source for organized testing
GITHUB_EVENTS = [
    SAMPLE_GITHUB_COMMIT,
    SAMPLE_GITHUB_PR_OPENED,
    SAMPLE_GITHUB_PR_MERGED,
    SAMPLE_GITHUB_COMMIT_COMMENT,
]

FITNESS_EVENTS = [
    SAMPLE_STRAVA_RUN,
    SAMPLE_APPLE_HEALTH_WORKOUT,
    SAMPLE_APPLE_HEALTH_STEPS,
]

MANUAL_EVENTS = [
    SAMPLE_MANUAL_HABIT,
    SAMPLE_MANUAL_GOAL_PROGRESS,
]

FUTURE_INTEGRATION_EVENTS = [
    SAMPLE_DUOLINGO_LESSON,
    SAMPLE_GOODREADS_BOOK,
]
