"""
Test Webhook → Goal Update Flow
This is the critical test to verify the end-to-end webhook processing
"""
import pytest
from uuid import uuid4

from app.models import User, Goal, EventRaw, Integration
from app.repositories.goal_repository import GoalRepository
from app.workers.goal_progress_worker import GoalProgressWorker
from app.types import GoalType, TrackingType, IntegrationSource


@pytest.mark.asyncio
async def test_webhook_updates_goal(db_session):
    """Test that a webhook event updates matching goals"""
    # Setup: Create user with GitHub integration
    user = User(id=uuid4(), email="test@example.com", medallions=0)
    db_session.add(user)
    await db_session.commit()
    
    integration = Integration(
        id=uuid4(),
        user_id=user.id,
        provider="github"
    )
    db_session.add(integration)
    await db_session.commit()
    
    # Create GitHub goal
    repo = GoalRepository(db_session)
    goal = Goal(
        user_id=user.id,
        name="Daily Commits",
        goal_type=GoalType.SHORT_TERM,
        integration_source=IntegrationSource.GITHUB,
        tracking_type=TrackingType.NUMERIC,
        target_value=10,
        unit="commits"
    )
    created_goal = await repo.create_goal(goal)
    assert created_goal.current_progress == 0
    
    # Simulate webhook event
    event_raw = EventRaw(
        id=uuid4(),
        integration_id=integration.id,
        external_event_id="test-delivery-123",
        payload={"type": "push", "commits": [{"sha": "abc123"}]},
        processed=False
    )
    db_session.add(event_raw)
    await db_session.commit()
    
    # Process the event (simulating worker)
    worker = GoalProgressWorker()
    # Manually call the update method
    await worker.update_goal_progress(db_session, created_goal, user, event_raw)
    
    # Verify goal was updated
    updated_goal = await repo.get_by_id(created_goal.id)
    assert updated_goal.current_progress == 1
    assert updated_goal.growth_stage == 0  # 10% - still baby


@pytest.mark.asyncio
async def test_webhook_updates_multiple_goals(db_session):
    """Test that one webhook event updates all matching goals"""
    # Setup user and integration
    user = User(id=uuid4(), email="test2@example.com", medallions=0)
    db_session.add(user)
    await db_session.commit()
    
    integration = Integration(
        id=uuid4(),
        user_id=user.id,
        provider="github"
    )
    db_session.add(integration)
    await db_session.commit()
    
    # Create 3 GitHub goals
    repo = GoalRepository(db_session)
    goals = []
    for i in range(3):
        goal = Goal(
            user_id=user.id,
            name=f"Goal {i}",
            goal_type=GoalType.SHORT_TERM,
            integration_source=IntegrationSource.GITHUB,
            tracking_type=TrackingType.NUMERIC,
            target_value=10,
            unit="commits"
        )
        created = await repo.create_goal(goal)
        goals.append(created)
    
    # Simulate webhook
    event_raw = EventRaw(
        id=uuid4(),
        integration_id=integration.id,
        external_event_id="test-delivery-456",
        payload={"type": "push"},
        processed=False
    )
    db_session.add(event_raw)
    await db_session.commit()
    
    # Process for all goals
    worker = GoalProgressWorker()
    for goal in goals:
        await worker.update_goal_progress(db_session, goal, user, event_raw)
    
    # Verify all goals updated
    for goal in goals:
        updated = await repo.get_by_id(goal.id)
        assert updated.current_progress == 1


@pytest.mark.asyncio
async def test_webhook_awards_medallions(db_session):
    """Test that webhook processing awards medallions"""
    # Setup
    user = User(id=uuid4(), email="test3@example.com", medallions=0)
    db_session.add(user)
    await db_session.commit()
    
    integration = Integration(
        id=uuid4(),
        user_id=user.id,
        provider="github"
    )
    db_session.add(integration)
    await db_session.commit()
    
    # Create goal
    repo = GoalRepository(db_session)
    goal = Goal(
        user_id=user.id,
        name="Test Goal",
        goal_type=GoalType.SHORT_TERM,
        integration_source=IntegrationSource.GITHUB,
        tracking_type=TrackingType.NUMERIC,
        target_value=10,
        unit="commits"
    )
    created_goal = await repo.create_goal(goal)
    
    # Process webhook
    event_raw = EventRaw(
        id=uuid4(),
        integration_id=integration.id,
        external_event_id="test-delivery-789",
        payload={},
        processed=False
    )
    db_session.add(event_raw)
    await db_session.commit()
    
    worker = GoalProgressWorker()
    await worker.update_goal_progress(db_session, created_goal, user, event_raw)
    
    # Check medallions awarded
    await db_session.refresh(user)
    assert user.medallions == 5  # First event of the day = 5 medallions
    
    updated_goal = await repo.get_by_id(created_goal.id)
    assert updated_goal.total_medallions_produced == 5
