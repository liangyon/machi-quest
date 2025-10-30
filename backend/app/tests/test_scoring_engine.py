"""
Tests for the scoring engine.

Verifies that events are correctly converted into score deltas
according to game rules.
"""
import pytest
from datetime import datetime
from uuid import uuid4

from app.services.scoring_engine import ScoringEngine
from app.services.event_normalizer import CanonicalEvent, EventType
from app.schemas.scoring import DeltaType
from app.tests.fixtures.events import TEST_USER_ID


class TestScoringEngine:
    """Test scoring engine rules."""
    
    def test_score_github_commit_gives_food(self):
        """Test that commits give 1 food point."""
        engine = ScoringEngine()
        pet_id = uuid4()
        event_raw_id = uuid4()
        
        event = CanonicalEvent(
            type=EventType.GITHUB_COMMIT,
            timestamp=datetime.utcnow(),
            user_id=TEST_USER_ID,
            value=1.0,
            meta={'commit_sha': 'abc123', 'repository': 'user/repo', 'branch': 'main'},
            event_raw_id=event_raw_id
        )
        
        deltas = engine.score_event(event, pet_id)
        
        assert len(deltas) == 1
        assert deltas[0].delta_type == DeltaType.FOOD
        assert deltas[0].amount == 1.0
        assert deltas[0].pet_id == pet_id
        assert deltas[0].event_id == event_raw_id
        assert deltas[0].meta['event_type'] == EventType.GITHUB_COMMIT
        assert deltas[0].meta['repository'] == 'user/repo'
        assert deltas[0].meta['branch'] == 'main'
    
    def test_score_pr_opened_gives_more_food(self):
        """Test that opening a PR gives 3 food points (more than commit)."""
        engine = ScoringEngine()
        pet_id = uuid4()
        event_raw_id = uuid4()
        
        event = CanonicalEvent(
            type=EventType.GITHUB_PR_OPENED,
            timestamp=datetime.utcnow(),
            user_id=TEST_USER_ID,
            value=1.0,
            meta={'pr_number': 42},
            event_raw_id=event_raw_id
        )
        
        deltas = engine.score_event(event, pet_id)
        
        assert len(deltas) == 1
        assert deltas[0].delta_type == DeltaType.FOOD
        assert deltas[0].amount == 3.0  # More than a single commit
        assert deltas[0].pet_id == pet_id
    
    def test_score_pr_merged_gives_multiple_deltas(self):
        """Test that PR merge gives both food and happiness."""
        engine = ScoringEngine()
        pet_id = uuid4()
        event_raw_id = uuid4()
        
        event = CanonicalEvent(
            type=EventType.GITHUB_PR_MERGED,
            timestamp=datetime.utcnow(),
            user_id=TEST_USER_ID,
            value=1.0,
            meta={'pr_number': 42, 'merged': True},
            event_raw_id=event_raw_id
        )
        
        deltas = engine.score_event(event, pet_id)
        
        assert len(deltas) == 2
        
        # Check food delta
        food_delta = [d for d in deltas if d.delta_type == DeltaType.FOOD][0]
        assert food_delta.amount == 5.0  # Big accomplishment
        assert food_delta.pet_id == pet_id
        
        # Check happiness delta
        happiness_delta = [d for d in deltas if d.delta_type == DeltaType.HAPPINESS][0]
        assert happiness_delta.amount == 3.0
        assert happiness_delta.pet_id == pet_id
        
        # Both should reference same event
        assert food_delta.event_id == event_raw_id
        assert happiness_delta.event_id == event_raw_id
    
    def test_score_manual_habit_uses_custom_value(self):
        """Test that manual habits use the event.value directly."""
        engine = ScoringEngine()
        pet_id = uuid4()
        event_raw_id = uuid4()
        
        # User logs a habit with custom value
        event = CanonicalEvent(
            type=EventType.MANUAL_HABIT,
            timestamp=datetime.utcnow(),
            user_id=TEST_USER_ID,
            value=10.0,  # Custom value
            meta={'title': 'Practiced guitar for 2 hours'},
            event_raw_id=event_raw_id
        )
        
        deltas = engine.score_event(event, pet_id)
        
        assert len(deltas) == 1
        assert deltas[0].delta_type == DeltaType.FOOD
        assert deltas[0].amount == 10.0  # Uses custom value
        assert deltas[0].meta['title'] == 'Practiced guitar for 2 hours'
    
    def test_unknown_event_type_returns_empty(self):
        """Test that unknown event types don't crash, just return no deltas."""
        engine = ScoringEngine()
        pet_id = uuid4()
        
        event = CanonicalEvent(
            type="unknown_event_type",
            timestamp=datetime.utcnow(),
            user_id=TEST_USER_ID,
            value=1.0,
            meta={},
            event_raw_id=uuid4()
        )
        
        deltas = engine.score_event(event, pet_id)
        
        assert len(deltas) == 0  # No scoring rule, no deltas
    
    def test_delta_timestamps_match_event(self):
        """Test that deltas preserve the event's timestamp."""
        engine = ScoringEngine()
        pet_id = uuid4()
        event_time = datetime(2025, 10, 28, 14, 30, 0)
        
        event = CanonicalEvent(
            type=EventType.GITHUB_COMMIT,
            timestamp=event_time,
            user_id=TEST_USER_ID,
            value=1.0,
            meta={'commit_sha': 'abc123'},
            event_raw_id=uuid4()
        )
        
        deltas = engine.score_event(event, pet_id)
        
        assert deltas[0].timestamp == event_time
    
    def test_multiple_commits_score_independently(self):
        """Test that each commit gets scored separately (not tested here, but documented)."""
        # This test documents expected behavior:
        # - Each commit in a push creates a separate CanonicalEvent
        # - Each CanonicalEvent gets scored independently
        # - So 3 commits = 3 separate score_event() calls = 3 food deltas
        
        engine = ScoringEngine()
        pet_id = uuid4()
        
        # Simulate 3 commits
        commit_count = 3
        total_food = 0
        
        for i in range(commit_count):
            event = CanonicalEvent(
                type=EventType.GITHUB_COMMIT,
                timestamp=datetime.utcnow(),
                user_id=TEST_USER_ID,
                value=1.0,
                meta={'commit_sha': f'commit{i}'},
                event_raw_id=uuid4()
            )
            
            deltas = engine.score_event(event, pet_id)
            total_food += deltas[0].amount
        
        assert total_food == 3.0  # 3 commits = 3 food


class TestDeltaTypeConstants:
    """Test that DeltaType constants are correct."""
    
    def test_delta_type_constants_exist(self):
        """Test that all expected delta types are defined."""
        assert DeltaType.FOOD == "food"
        assert DeltaType.CURRENCY == "currency"
        assert DeltaType.HAPPINESS == "happiness"
        assert DeltaType.HEALTH == "health"
    
    def test_scoring_engine_uses_constants(self):
        """Test that scoring engine uses DeltaType constants (not strings)."""
        engine = ScoringEngine()
        pet_id = uuid4()
        
        event = CanonicalEvent(
            type=EventType.GITHUB_COMMIT,
            timestamp=datetime.utcnow(),
            user_id=TEST_USER_ID,
            value=1.0,
            meta={'commit_sha': 'abc123'},
            event_raw_id=uuid4()
        )
        
        deltas = engine.score_event(event, pet_id)
        
        # Should use constant, not hardcoded string
        assert deltas[0].delta_type == DeltaType.FOOD
