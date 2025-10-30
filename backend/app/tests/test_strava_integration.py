"""
Tests for Strava Integration

Tests the complete Strava flow: webhook → normalize → score → state update
"""
import pytest
from uuid import uuid4
from datetime import datetime

from app.db.models import User, Pet, EventRaw, Integration
from app.services.normalizers.strava import normalize_strava_activity
from app.services.scoring_engine import ScoringEngine
from app.services.event_normalizer import EventType
from app.schemas.scoring import DeltaType
from app.workers.state_worker import StateUpdateWorker


class TestStravaIntegration:
    """Test Strava integration end-to-end."""
    
    def test_strava_run_to_pet_food(self, db_session):
        """
        Test complete flow: Strava run → Pet gets food + happiness.
        
        Scenario: User goes for a 5km run (30 minutes)
        """
        # Create user with Strava integration
        user = User(
            id=uuid4(),
            email="runner@example.com",
            github_id=None  # Strava-only user
        )
        
        strava_integration = Integration(
            id=uuid4(),
            user_id=user.id,
            provider='strava',
            meta_data={'strava_user_id': '123456'}
        )
        
        pet = Pet(
            id=uuid4(),
            user_id=user.id,
            name="Running Buddy",
            species="dog",
            state_json={
                "food": 20,
                "currency": 10,
                "happiness": 60,
                "health": 100,
                "processed_events": []
            },
            version=1
        )
        
        db_session.add(user)
        db_session.add(strava_integration)
        db_session.add(pet)
        db_session.commit()
        
        # Simulate Strava activity payload
        activity_payload = {
            'id': 98765,
            'name': 'Morning Run',
            'type': 'Run',
            'distance': 5210,  # 5.21 km
            'moving_time': 1800,  # 30 minutes
            'total_elevation_gain': 45,
            'start_date': '2025-10-29T06:00:00Z',
            'kudos_count': 3
        }
        
        # Normalize
        canonical_events = normalize_strava_activity(
            activity_payload,
            user.id,
            uuid4()
        )
        
        assert len(canonical_events) == 1
        canon = canonical_events[0]
        assert canon.type == EventType.STRAVA_ACTIVITY
        
        # Value should have bonuses:
        # Base 1.0 + distance (5.21/5 = 1.04) + duration (30/30 = 1.0) ≈ 3.04
        assert canon.value > 3.0
        
        # Score
        scoring_engine = ScoringEngine()
        deltas = scoring_engine.score_event(canon, pet.id)
        
        # Should get food AND happiness
        assert len(deltas) == 2
        
        food_delta = [d for d in deltas if d.delta_type == DeltaType.FOOD][0]
        happiness_delta = [d for d in deltas if d.delta_type == DeltaType.HAPPINESS][0]
        
        # Food: value (~3.04) * STRAVA_ACTIVITY_FOOD (2.0) ≈ 6.08
        assert food_delta.amount >= 6.0
        assert happiness_delta.amount == 1.0
        
        # Apply to state
        worker = StateUpdateWorker()
        for delta in deltas:
            delta_data = {
                'event_id': str(uuid4()),
                'delta_type': delta.delta_type,
                'amount': str(delta.amount),
                'pet_id': str(pet.id)
            }
            worker.apply_delta(pet.id, delta_data, db_session)
        
        db_session.refresh(pet)
        
        # Verify final state
        # Started with: food=20, happiness=60
        # Added: food ~6, happiness +1
        assert pet.state_json['food'] >= 26.0
        assert pet.state_json['happiness'] == 61
    
    def test_strava_long_ride_with_overflow(self, db_session):
        """
        Test that a long Strava ride can cause food overflow.
        
        Scenario: 100km bike ride (4 hours) → lots of food → overflow to currency
        """
        user = User(id=uuid4(), email="cyclist@example.com")
        pet = Pet(
            id=uuid4(),
            user_id=user.id,
            name="Cyclist Cat",
            state_json={
                "food": 85,  # Already high
                "currency": 5,
                "happiness": 70,
                "health": 100,
                "processed_events": [],
                "food_cap": 100,
                "overflow_to_currency_rate": 0.5
            },
            version=1
        )
        
        db_session.add(user)
        db_session.add(pet)
        db_session.commit()
        
        # Big ride
        activity_payload = {
            'id': 55555,
            'type': 'Ride',
            'distance': 100000,  # 100 km!
            'moving_time': 14400,  # 4 hours
            'start_date': '2025-10-29T08:00:00Z'
        }
        
        # Normalize
        canonical_events = normalize_strava_activity(activity_payload, user.id, uuid4())
        canon = canonical_events[0]
        
        # Value: 1.0 + (100/5 = 20) + (240min/30 = 8) = 29.0
        assert canon.value >= 29.0
        
        # Score
        scoring_engine = ScoringEngine()
        deltas = scoring_engine.score_event(canon, pet.id)
        
        food_delta = [d for d in deltas if d.delta_type == DeltaType.FOOD][0]
        # 29.0 * 2.0 = 58 food!
        assert food_delta.amount >= 58.0
        
        # Apply
        worker = StateUpdateWorker()
        delta_data = {
            'event_id': str(uuid4()),
            'delta_type': DeltaType.FOOD,
            'amount': str(food_delta.amount),
            'pet_id': str(pet.id)
        }
        worker.apply_delta(pet.id, delta_data, db_session)
        
        db_session.refresh(pet)
        
        # Food capped at 100
        assert pet.state_json['food'] == 100
        
        # Overflow converted to currency
        # Started with 85, added ~58 = 143
        # Capped at 100, overflow = 43
        # Currency: 5 + (43 * 0.5) = 26.5
        assert pet.state_json['currency'] > 20.0
