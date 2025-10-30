"""
Tests for the State Update Worker.

Tests idempotency, optimistic locking, food overflow, and state updates.
"""
import pytest
from datetime import datetime
from uuid import uuid4

from app.workers.state_worker import StateUpdateWorker, FOOD_CAP, OVERFLOW_TO_CURRENCY_RATE
from app.db.models import Pet, User
from app.schemas.scoring import DeltaType


class TestStateUpdateWorker:
    """Test state update worker functionality."""
    
    def test_apply_food_delta(self, db_session):
        """Test applying a food delta to pet state."""
        # Create user and pet
        user = User(
            id=uuid4(),
            email="test@example.com",
            github_id="123"
        )
        pet = Pet(
            id=uuid4(),
            user_id=user.id,
            name="Test Pet",
            state_json={"food": 10, "currency": 0, "happiness": 50, "health": 100, "processed_events": []},
            version=1
        )
        db_session.add(user)
        db_session.add(pet)
        db_session.commit()
        
        # Apply food delta
        worker = StateUpdateWorker()
        delta_data = {
            'event_id': str(uuid4()),
            'delta_type': DeltaType.FOOD,
            'amount': '5.0'
        }
        
        result = worker.apply_delta(pet.id, delta_data, db_session)
        
        assert result is True
        
        # Refresh pet from DB
        db_session.refresh(pet)
        
        assert pet.state_json['food'] == 15.0
        assert pet.version == 2
        # Idempotency now uses event_id:delta_type format
        expected_key = f"{delta_data['event_id']}:{DeltaType.FOOD}"
        assert expected_key in pet.state_json['processed_events']
    
    def test_idempotency_prevents_double_processing(self, db_session):
        """Test that same delta is not processed twice."""
        user = User(id=uuid4(), email="test@example.com", github_id="123")
        event_id = str(uuid4())
        delta_key = f"{event_id}:{DeltaType.FOOD}"  # New format
        pet = Pet(
            id=uuid4(),
            user_id=user.id,
            name="Test Pet",
            state_json={
                "food": 10,
                "currency": 0,
                "happiness": 50,
                "health": 100,
                "processed_events": [delta_key]  # Already processed (new format)
            },
            version=1
        )
        db_session.add(user)
        db_session.add(pet)
        db_session.commit()
        
        worker = StateUpdateWorker()
        delta_data = {
            'event_id': event_id,
            'delta_type': DeltaType.FOOD,
            'amount': '5.0'
        }
        
        # Try to process same event again
        result = worker.apply_delta(pet.id, delta_data, db_session)
        
        assert result is False  # Not applied due to idempotency
        
        db_session.refresh(pet)
        assert pet.state_json['food'] == 10  # Unchanged
        assert pet.version == 1  # Version unchanged
    
    def test_food_overflow_converts_to_currency(self, db_session):
        """Test that food over cap converts to currency."""
        user = User(id=uuid4(), email="test@example.com", github_id="123")
        pet = Pet(
            id=uuid4(),
            user_id=user.id,
            name="Test Pet",
            state_json={
                "food": 95,  # Near cap
                "currency": 10,
                "happiness": 50,
                "health": 100,
                "processed_events": [],
                "food_cap": FOOD_CAP,
                "overflow_to_currency_rate": OVERFLOW_TO_CURRENCY_RATE
            },
            version=1
        )
        db_session.add(user)
        db_session.add(pet)
        db_session.commit()
        
        worker = StateUpdateWorker()
        delta_data = {
            'event_id': str(uuid4()),
            'delta_type': DeltaType.FOOD,
            'amount': '10.0'  # Would make 105, over cap
        }
        
        worker.apply_delta(pet.id, delta_data, db_session)
        
        db_session.refresh(pet)
        
        # Food should be capped at 100
        assert pet.state_json['food'] == FOOD_CAP
        
        # Overflow: 5 food * 0.5 rate = 2.5 currency
        expected_currency = 10 + (5 * OVERFLOW_TO_CURRENCY_RATE)
        assert pet.state_json['currency'] == expected_currency
    
    def test_happiness_clamped_to_0_100(self, db_session):
        """Test that happiness stays between 0 and 100."""
        user = User(id=uuid4(), email="test@example.com", github_id="123")
        pet = Pet(
            id=uuid4(),
            user_id=user.id,
            name="Test Pet",
            state_json={
                "food": 10,
                "currency": 0,
                "happiness": 95,
                "health": 100,
                "processed_events": []
            },
            version=1
        )
        db_session.add(user)
        db_session.add(pet)
        db_session.commit()
        
        worker = StateUpdateWorker()
        
        # Try to add happiness that would exceed 100
        delta_data = {
            'event_id': str(uuid4()),
            'delta_type': DeltaType.HAPPINESS,
            'amount': '10.0'
        }
        
        worker.apply_delta(pet.id, delta_data, db_session)
        
        db_session.refresh(pet)
        assert pet.state_json['happiness'] == 100  # Clamped
    
    def test_currency_delta(self, db_session):
        """Test applying currency delta."""
        user = User(id=uuid4(), email="test@example.com", github_id="123")
        pet = Pet(
            id=uuid4(),
            user_id=user.id,
            name="Test Pet",
            state_json={
                "food": 10,
                "currency": 50,
                "happiness": 50,
                "health": 100,
                "processed_events": []
            },
            version=1
        )
        db_session.add(user)
        db_session.add(pet)
        db_session.commit()
        
        worker = StateUpdateWorker()
        delta_data = {
            'event_id': str(uuid4()),
            'delta_type': DeltaType.CURRENCY,
            'amount': '25.0'
        }
        
        worker.apply_delta(pet.id, delta_data, db_session)
        
        db_session.refresh(pet)
        assert pet.state_json['currency'] == 75.0
    
    def test_default_state_initialization(self, db_session):
        """Test that worker initializes default state for new pets."""
        user = User(id=uuid4(), email="test@example.com", github_id="123")
        pet = Pet(
            id=uuid4(),
            user_id=user.id,
            name="Test Pet",
            state_json=None,  # No state yet
            version=1
        )
        db_session.add(user)
        db_session.add(pet)
        db_session.commit()
        
        worker = StateUpdateWorker()
        delta_data = {
            'event_id': str(uuid4()),
            'delta_type': DeltaType.FOOD,
            'amount': '5.0'
        }
        
        worker.apply_delta(pet.id, delta_data, db_session)
        
        db_session.refresh(pet)
        
        # Should have initialized with defaults
        assert pet.state_json['food'] == 5.0
        assert pet.state_json['currency'] == 0
        assert pet.state_json['happiness'] == 50
        assert pet.state_json['health'] == 100
        assert 'processed_events' in pet.state_json
    
    def test_processed_events_limit(self, db_session):
        """Test that processed_events list is limited to 1000 entries."""
        user = User(id=uuid4(), email="test@example.com", github_id="123")
        
        # Create pet with 1000 processed events
        processed_events = [str(uuid4()) for _ in range(1000)]
        pet = Pet(
            id=uuid4(),
            user_id=user.id,
            name="Test Pet",
            state_json={
                "food": 10,
                "currency": 0,
                "happiness": 50,
                "health": 100,
                "processed_events": processed_events
            },
            version=1
        )
        db_session.add(user)
        db_session.add(pet)
        db_session.commit()
        
        worker = StateUpdateWorker()
        delta_data = {
            'event_id': str(uuid4()),
            'delta_type': DeltaType.FOOD,
            'amount': '1.0'
        }
        
        worker.apply_delta(pet.id, delta_data, db_session)
        
        db_session.refresh(pet)
        
        # List should still be limited to 1000
        assert len(pet.state_json['processed_events']) == 1000
        
        # Newest delta should be in list (event_id:delta_type format)
        expected_key = f"{delta_data['event_id']}:{DeltaType.FOOD}"
        assert expected_key in pet.state_json['processed_events']
        
        # Oldest event should have been dropped
        assert processed_events[0] not in pet.state_json['processed_events']
