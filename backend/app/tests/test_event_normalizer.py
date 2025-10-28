"""
Unit tests for the event normalizer.

These tests verify that external events are correctly transformed
into canonical events.
"""
import pytest
from datetime import datetime
from uuid import uuid4

from app.services.event_normalizer import (
    CanonicalEvent,
    EventType,
    validate_canonical_event,
)
from app.services.normalizers.github import (
    normalize_github_push,
    normalize_github_pull_request,
    normalize_github_commit_comment,
)
from app.services.normalizers.manual import normalize_manual_event
from app.tests.fixtures.events import (
    TEST_USER_ID,
    SAMPLE_GITHUB_COMMIT,
    ALL_SAMPLE_EVENTS,
)


class TestCanonicalEventValidation:
    """Test CanonicalEvent validation logic."""
    
    def test_valid_event_passes_validation(self):
        """Test that a valid event passes validation."""
        event = SAMPLE_GITHUB_COMMIT
        # Should not raise
        validate_canonical_event(event)
    
    def test_missing_commit_sha_fails_validation(self):
        """Test that GitHub commit without commit_sha fails validation."""
        event = CanonicalEvent(
            type=EventType.GITHUB_COMMIT,
            timestamp=datetime.utcnow(),
            user_id=TEST_USER_ID,
            value=1.0,
            meta={'repository': 'user/repo'}  # Missing commit_sha
        )
        
        with pytest.raises(ValueError, match="commit_sha"):
            validate_canonical_event(event)
    
    def test_missing_pr_number_fails_validation(self):
        """Test that GitHub PR without pr_number fails validation."""
        event = CanonicalEvent(
            type=EventType.GITHUB_PR_OPENED,
            timestamp=datetime.utcnow(),
            user_id=TEST_USER_ID,
            value=1.0,
            meta={'title': 'Test PR'}  # Missing pr_number
        )
        
        with pytest.raises(ValueError, match="pr_number"):
            validate_canonical_event(event)
    
    def test_missing_title_for_manual_habit_fails(self):
        """Test that manual habit without title fails validation."""
        event = CanonicalEvent(
            type=EventType.MANUAL_HABIT,
            timestamp=datetime.utcnow(),
            user_id=TEST_USER_ID,
            value=1.0,
            meta={'category': 'music'}  # Missing title
        )
        
        with pytest.raises(ValueError, match="title"):
            validate_canonical_event(event)
    
    def test_negative_value_fails_validation(self):
        """Test that negative value fails validation."""
        with pytest.raises(ValueError, match="negative"):
            CanonicalEvent(
                type=EventType.GITHUB_COMMIT,
                timestamp=datetime.utcnow(),
                user_id=TEST_USER_ID,
                value=-1.0,  # Invalid
                meta={'commit_sha': 'abc123'}
            )
    
    def test_all_sample_events_are_valid(self):
        """Test that all sample events pass validation."""
        for event in ALL_SAMPLE_EVENTS:
            # Should not raise
            validate_canonical_event(event)


class TestGitHubPushNormalizer:
    """Test GitHub push event normalization."""
    
    def test_normalize_single_commit(self):
        """Test normalizing a GitHub push with one commit."""
        user_id = uuid4()
        
        payload = {
            'commits': [
                {
                    'id': 'abc123',
                    'message': 'Fix bug in pet animation',
                    'timestamp': '2025-10-27T14:30:00Z',
                    'url': 'https://github.com/user/repo/commit/abc123'
                }
            ],
            'repository': {'full_name': 'user/machi-quest'},
            'ref': 'refs/heads/main'
        }
        
        events = normalize_github_push(payload, user_id)
        
        assert len(events) == 1
        assert events[0].type == EventType.GITHUB_COMMIT
        assert events[0].user_id == user_id
        assert events[0].value == 1.0
        assert events[0].meta['commit_sha'] == 'abc123'
        assert events[0].meta['repository'] == 'user/machi-quest'
        assert events[0].meta['branch'] == 'main'
        assert events[0].meta['source'] == 'github'
    
    def test_normalize_multiple_commits(self):
        """Test that push with 3 commits creates 3 events."""
        user_id = uuid4()
        
        payload = {
            'commits': [
                {'id': 'commit1', 'message': 'First', 'timestamp': '2025-10-27T14:30:00Z'},
                {'id': 'commit2', 'message': 'Second', 'timestamp': '2025-10-27T14:31:00Z'},
                {'id': 'commit3', 'message': 'Third', 'timestamp': '2025-10-27T14:32:00Z'},
            ],
            'repository': {'full_name': 'user/repo'},
            'ref': 'refs/heads/feature-branch'
        }
        
        events = normalize_github_push(payload, user_id)
        
        assert len(events) == 3
        assert events[0].meta['commit_sha'] == 'commit1'
        assert events[1].meta['commit_sha'] == 'commit2'
        assert events[2].meta['commit_sha'] == 'commit3'
        assert all(e.meta['branch'] == 'feature-branch' for e in events)
    
    def test_normalize_empty_commits_list(self):
        """Test that push with no commits returns empty list."""
        user_id = uuid4()
        
        payload = {
            'commits': [],
            'repository': {'full_name': 'user/repo'},
            'ref': 'refs/heads/main'
        }
        
        events = normalize_github_push(payload, user_id)
        
        assert len(events) == 0
    
    def test_truncate_long_commit_message(self):
        """Test that long commit messages are truncated."""
        user_id = uuid4()
        long_message = 'A' * 1000  # 1000 character message
        
        payload = {
            'commits': [
                {
                    'id': 'abc123',
                    'message': long_message,
                    'timestamp': '2025-10-27T14:30:00Z',
                }
            ],
            'repository': {'full_name': 'user/repo'},
            'ref': 'refs/heads/main'
        }
        
        events = normalize_github_push(payload, user_id)
        
        assert len(events[0].meta['message']) == 500


class TestGitHubPullRequestNormalizer:
    """Test GitHub pull request event normalization."""
    
    def test_normalize_pr_opened(self):
        """Test normalizing a PR opened event."""
        user_id = uuid4()
        
        payload = {
            'action': 'opened',
            'pull_request': {
                'number': 42,
                'title': 'Add feature',
                'html_url': 'https://github.com/user/repo/pull/42',
                'created_at': '2025-10-27T15:00:00Z',
                'merged': False
            },
            'repository': {'full_name': 'user/repo'}
        }
        
        events = normalize_github_pull_request(payload, user_id)
        
        assert len(events) == 1
        assert events[0].type == EventType.GITHUB_PR_OPENED
        assert events[0].meta['pr_number'] == 42
        assert events[0].meta['action'] == 'opened'
        assert events[0].meta['merged'] is False
    
    def test_normalize_pr_merged(self):
        """Test normalizing a PR merged event."""
        user_id = uuid4()
        
        payload = {
            'action': 'closed',
            'pull_request': {
                'number': 42,
                'title': 'Add feature',
                'html_url': 'https://github.com/user/repo/pull/42',
                'created_at': '2025-10-27T15:00:00Z',
                'merged': True
            },
            'repository': {'full_name': 'user/repo'}
        }
        
        events = normalize_github_pull_request(payload, user_id)
        
        assert len(events) == 1
        assert events[0].type == EventType.GITHUB_PR_MERGED
        assert events[0].meta['merged'] is True
    
    def test_normalize_pr_closed_not_merged(self):
        """Test normalizing a PR closed without merge."""
        user_id = uuid4()
        
        payload = {
            'action': 'closed',
            'pull_request': {
                'number': 42,
                'title': 'Add feature',
                'html_url': 'https://github.com/user/repo/pull/42',
                'created_at': '2025-10-27T15:00:00Z',
                'merged': False
            },
            'repository': {'full_name': 'user/repo'}
        }
        
        events = normalize_github_pull_request(payload, user_id)
        
        assert len(events) == 1
        assert events[0].type == EventType.GITHUB_PR_CLOSED
        assert events[0].meta['merged'] is False
    
    def test_normalize_pr_unsupported_action(self):
        """Test that unsupported PR actions return empty list."""
        user_id = uuid4()
        
        payload = {
            'action': 'synchronize',  # Not supported
            'pull_request': {
                'number': 42,
                'title': 'Add feature',
                'created_at': '2025-10-27T15:00:00Z'
            },
            'repository': {'full_name': 'user/repo'}
        }
        
        events = normalize_github_pull_request(payload, user_id)
        
        assert len(events) == 0


class TestGitHubCommitCommentNormalizer:
    """Test GitHub commit comment event normalization."""
    
    def test_normalize_commit_comment(self):
        """Test normalizing a commit comment event."""
        user_id = uuid4()
        
        payload = {
            'comment': {
                'commit_id': 'abc123',
                'body': 'Great work on this!',
                'html_url': 'https://github.com/user/repo/commit/abc123#comment',
                'created_at': '2025-10-27T14:45:00Z'
            },
            'repository': {'full_name': 'user/repo'}
        }
        
        events = normalize_github_commit_comment(payload, user_id)
        
        assert len(events) == 1
        assert events[0].type == EventType.GITHUB_COMMIT_COMMENT
        assert events[0].meta['commit_sha'] == 'abc123'
        assert events[0].meta['comment_body'] == 'Great work on this!'
        assert events[0].meta['repository'] == 'user/repo'


class TestManualEventNormalizer:
    """Test manual event normalization."""
    
    def test_normalize_manual_habit(self):
        """Test creating a manual habit event."""
        user_id = uuid4()
        
        event = normalize_manual_event(
            event_type=EventType.MANUAL_HABIT,
            title='Practiced guitar',
            user_id=user_id,
            value=1.0,
            meta={'duration_minutes': 30, 'category': 'music'}
        )
        
        assert event.type == EventType.MANUAL_HABIT
        assert event.user_id == user_id
        assert event.value == 1.0
        assert event.meta['title'] == 'Practiced guitar'
        assert event.meta['duration_minutes'] == 30
        assert event.meta['category'] == 'music'
        assert event.meta['source'] == 'manual'
    
    def test_normalize_manual_event_with_custom_timestamp(self):
        """Test creating a manual event with custom timestamp."""
        user_id = uuid4()
        custom_time = datetime(2025, 10, 27, 12, 0, 0)
        
        event = normalize_manual_event(
            event_type=EventType.MANUAL_HABIT,
            title='Morning meditation',
            user_id=user_id,
            timestamp=custom_time
        )
        
        assert event.timestamp == custom_time
    
    def test_normalize_manual_event_defaults_to_now(self):
        """Test that manual event without timestamp defaults to now."""
        user_id = uuid4()
        before = datetime.utcnow()
        
        event = normalize_manual_event(
            event_type=EventType.MANUAL_HABIT,
            title='Test habit',
            user_id=user_id
        )
        
        after = datetime.utcnow()
        
        assert before <= event.timestamp <= after
    
    def test_normalize_manual_goal_progress(self):
        """Test creating a manual goal progress event."""
        user_id = uuid4()
        
        event = normalize_manual_event(
            event_type=EventType.MANUAL_GOAL_PROGRESS,
            title='Read 50 pages',
            user_id=user_id,
            value=50.0,
            meta={'quantity': 50, 'unit': 'pages', 'category': 'reading'}
        )
        
        assert event.type == EventType.MANUAL_GOAL_PROGRESS
        assert event.value == 50.0
        assert event.meta['quantity'] == 50
        assert event.meta['unit'] == 'pages'
