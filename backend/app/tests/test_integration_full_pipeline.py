"""
Integration Tests - Full Pipeline

Tests the complete flow: Webhook → Event → ScoreDelta → Pet State

This simulates a GitHub push webhook and verifies:
1. EventRaw is created
2. Events are normalized and created
3. ScoreDeltas are generated
4. Pet state is updated correctly
5. Cache is invalidated
"""
import pytest
from uuid import uuid4
import time

from app.db.models import User, Pet, EventRaw, Event
from app.services.event_normalizer import EventType
from app.services.normalizers.github import normalize_github_push
from app.services.scoring_engine import ScoringEngine
from app.workers.state_worker import StateUpdateWorker
from app.schemas.scoring import DeltaType


class TestFullPipeline:
    """Test complete ingestion → scoring → state pipeline."""
    
    def test_github_push_to_pet_state(self, db_session):
        """
        End-to-end test: GitHub push → Pet gets food.
        
        Steps:
        1. Create user and pet
        2. Simulate GitHub push with 3 commits
        3. Normalize events
        4. Score events
        5. Apply deltas to pet state
        6. Verify final state is correct
        """
        # Step 1: Create test user and pet
        user = User(
            id=uuid4(),
            email="developer@example.com",
            github_id="987654321",
            github_username="testdev"
        )
        pet = Pet(
            id=uuid4(),
            user_id=user.id,
            name="Code Buddy",
            species="cat",
            state_json={
                "food": 10,
                "currency": 5,
                "happiness": 50,
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
        
        # Step 2: Create EventRaw (simulating webhook)
        event_raw = EventRaw(
            id=uuid4(),
            external_event_id="test-delivery-123",
            payload={
                "commits": [
                    {
                        "id": "commit1",
                        "message": "Add feature A",
                        "timestamp": "2025-10-29T14:00:00Z",
                        "url": "https://github.com/user/repo/commit/1"
                    },
                    {
                        "id": "commit2",
                        "message": "Fix bug B",
                        "timestamp": "2025-10-29T14:05:00Z",
                        "url": "https://github.com/user/repo/commit/2"
                    },
                    {
                        "id": "commit3",
                        "message": "Update docs",
                        "timestamp": "2025-10-29T14:10:00Z",
                        "url": "https://github.com/user/repo/commit/3"
                    }
                ],
                "repository": {"full_name": "testdev/awesome-project"},
                "ref": "refs/heads/main"
            },
            processed=False
        )
        db_session.add(event_raw)
        db_session.commit()
        
        # Step 3: Normalize events
        canonical_events = normalize_github_push(
            event_raw.payload,
            user.id,
            event_raw.id
        )
        
        assert len(canonical_events) == 3  # 3 commits
        
        # Step 4: Create Event records and score them
        scoring_engine = ScoringEngine()
        total_food = 0
        
        for canon in canonical_events:
            # Create Event DB record
            event = Event(
                id=uuid4(),
                event_raw_id=event_raw.id,
                user_id=canon.user_id,
                pet_id=pet.id,
                type=canon.type,
                value=canon.value,
                meta=canon.meta,
                scored=True
            )
            db_session.add(event)
            db_session.flush()
            
            # Score the event
            canon.pet_id = pet.id
            score_deltas = scoring_engine.score_event(canon, pet.id)
            
            # Step 5: Apply deltas to pet state
            worker = StateUpdateWorker()
            for delta in score_deltas:
                delta_data = {
                    'event_id': str(event.id),
                    'delta_type': delta.delta_type,
                    'amount': str(delta.amount),
                    'pet_id': str(pet.id)
                }
                worker.apply_delta(pet.id, delta_data, db_session)
                
                if delta.delta_type == DeltaType.FOOD:
                    total_food += delta.amount
        
        event_raw.processed = True
        db_session.commit()
        
        # Step 6: Verify final state
        db_session.refresh(pet)
        
        # Started with 10 food + 3 commits (3 food) = 13 food
        assert pet.state_json['food'] == 13.0
        assert pet.state_json['currency'] == 5.0  # No overflow
        assert pet.state_json['happiness'] == 50  # Unchanged
        
        # Verify 3 events were processed
        event_count = db_session.query(Event).filter(Event.pet_id == pet.id).count()
        assert event_count == 3
        
        # Verify version incremented (once per delta)
        assert pet.version == 4  # 1 + 3 deltas
    
    def test_pr_merge_gives_food_and_happiness(self, db_session):
        """
        Test that PR merge gives both food and happiness.
        """
        # Create test data
        user = User(id=uuid4(), email="dev@example.com", github_id="123")
        pet = Pet(
            id=uuid4(),
            user_id=user.id,
            name="Test Pet",
            state_json={
                "food": 20,
                "currency": 10,
                "happiness": 50,
                "health": 100,
                "processed_events": []
            },
            version=1
        )
        db_session.add(user)
        db_session.add(pet)
        db_session.commit()
        
        # Create Event for PR merge
        event = Event(
            id=uuid4(),
            user_id=user.id,
            pet_id=pet.id,
            type=EventType.GITHUB_PR_MERGED,
            value=1.0,
            meta={'pr_number': 42, 'merged': True},
            scored=True
        )
        db_session.add(event)
        db_session.flush()
        
        # Score and apply
        from app.services.event_normalizer import CanonicalEvent
        from datetime import datetime
        
        canon = CanonicalEvent(
            type=EventType.GITHUB_PR_MERGED,
            timestamp=datetime.utcnow(),
            user_id=user.id,
            value=1.0,
            meta={'pr_number': 42},
            pet_id=pet.id,
            event_raw_id=event.id
        )
        
        scoring_engine = ScoringEngine()
        deltas = scoring_engine.score_event(canon, pet.id)
        
        # Should get 2 deltas: food and happiness
        assert len(deltas) == 2
        
        worker = StateUpdateWorker()
        for delta in deltas:
            delta_data = {
                'event_id': str(event.id),
                'delta_type': delta.delta_type,
                'amount': str(delta.amount),
                'pet_id': str(pet.id)
            }
            worker.apply_delta(pet.id, delta_data, db_session)
        
        db_session.refresh(pet)
        
        # Verify: Started with food=20, should get +5
        assert pet.state_json['food'] == 25.0
        
        # Verify: Started with happiness=50, should get +3
        assert pet.state_json['happiness'] == 53.0
    
    def test_food_overflow_scenario(self, db_session):
        """
        Test that food overflow converts to currency.
        
        Scenario: Pet has 95 food, gets 10 more → overflow
        """
        user = User(id=uuid4(), email="dev@example.com", github_id="123")
        pet = Pet(
            id=uuid4(),
            user_id=user.id,
            name="Hungry Pet",
            state_json={
                "food": 95,  # Near cap
                "currency": 0,
                "happiness": 50,
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
        
        # Apply 10 food delta
        worker = StateUpdateWorker()
        delta_data = {
            'event_id': str(uuid4()),
            'delta_type': DeltaType.FOOD,
            'amount': '10.0',
            'pet_id': str(pet.id)
        }
        
        worker.apply_delta(pet.id, delta_data, db_session)
        
        db_session.refresh(pet)
        
        # Food capped at 100
        assert pet.state_json['food'] == 100
        
        # Overflow: 5 food * 0.5 rate = 2.5 currency
        assert pet.state_json['currency'] == 2.5
    
    def test_idempotency_in_full_pipeline(self, db_session):
        """
        Test that processing same event twice doesn't double-add points.
        
        This is critical for data integrity!
        """
        user = User(id=uuid4(), email="dev@example.com", github_id="123")
        pet = Pet(
            id=uuid4(),
            user_id=user.id,
            name="Test Pet",
            state_json={
                "food": 10,
                "currency": 0,
                "happiness": 50,
                "health": 100,
                "processed_events": []
            },
            version=1
        )
        db_session.add(user)
        db_session.add(pet)
        db_session.commit()
        
        event_id = str(uuid4())
        delta_data = {
            'event_id': event_id,
            'delta_type': DeltaType.FOOD,
            'amount': '5.0',
            'pet_id': str(pet.id)
        }
        
        worker = StateUpdateWorker()
        
        # Process once
        result1 = worker.apply_delta(pet.id, delta_data, db_session)
        assert result1 is True
        
        db_session.refresh(pet)
        assert pet.state_json['food'] == 15.0
        first_version = pet.version
        
        # Try to process same event again
        result2 = worker.apply_delta(pet.id, delta_data, db_session)
        assert result2 is False  # Idempotency check prevented reprocessing
        
        db_session.refresh(pet)
        assert pet.state_json['food'] == 15.0  # Unchanged!
        assert pet.version == first_version  # Version unchanged!
