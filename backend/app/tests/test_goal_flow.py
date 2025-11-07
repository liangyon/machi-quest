"""
Test Goal Lifecycle - Create, update progress, complete
"""
import pytest
from datetime import datetime
from uuid import uuid4

from app.models import User, Goal, Avatar
from app.repositories.goal_repository import GoalRepository
from app.types import GoalType, TrackingType, IntegrationSource


@pytest.mark.asyncio
async def test_create_goal(db_session):
    """Test creating a new goal"""
    # Create test user and avatar
    user = User(
        id=uuid4(),
        email="test@example.com",
        medallions=0
    )
    db_session.add(user)
    await db_session.commit()
    
    avatar = Avatar(user_id=user.id, species="default")
    db_session.add(avatar)
    await db_session.commit()
    
    # Create goal
    repo = GoalRepository(db_session)
    goal = Goal(
        user_id=user.id,
        name="Daily Commits",
        goal_type=GoalType.SHORT_TERM,
        integration_source=IntegrationSource.GITHUB,
        tracking_type=TrackingType.NUMERIC,
        target_value=30,
        unit="days"
    )
    
    created = await repo.create_goal(goal)
    
    assert created.id is not None
    assert created.current_progress == 0
    assert created.growth_stage == 0
    assert not created.is_crowned


@pytest.mark.asyncio
async def test_goal_progress_and_completion(db_session):
    """Test goal progress updates and completion"""
    # Setup
    user = User(id=uuid4(), email="test2@example.com", medallions=0)
    db_session.add(user)
    await db_session.commit()
    
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
    created = await repo.create_goal(goal)
    
    # Test progress updates
    await repo.increment_progress(created.id, amount=3)
    goal = await repo.get_by_id(created.id)
    assert goal.current_progress == 3
    assert goal.growth_stage == 0  # 30% - still baby
    
    await repo.increment_progress(created.id, amount=4)
    goal = await repo.get_by_id(created.id)
    assert goal.current_progress == 7
    assert goal.growth_stage == 2  # 70% - adult
    
    # Complete goal
    await repo.increment_progress(created.id, amount=3)
    goal = await repo.get_by_id(created.id)
    assert goal.current_progress == 10
    assert goal.growth_stage == 3  # 100% - crowned
    assert goal.is_crowned
    assert goal.is_completed


@pytest.mark.asyncio
async def test_max_goals_limit(db_session):
    """Test that users cannot create more than 5 active goals"""
    user = User(id=uuid4(), email="test3@example.com", medallions=0)
    db_session.add(user)
    await db_session.commit()
    
    repo = GoalRepository(db_session)
    
    # Create 5 goals (should succeed)
    for i in range(5):
        goal = Goal(
            user_id=user.id,
            name=f"Goal {i}",
            goal_type=GoalType.SHORT_TERM,
            integration_source=IntegrationSource.MANUAL,
            tracking_type=TrackingType.NUMERIC,
            target_value=10,
            unit="tasks"
        )
        await repo.create_goal(goal)
    
    # Try to create 6th goal (should fail)
    goal = Goal(
        user_id=user.id,
        name="Goal 6",
        goal_type=GoalType.SHORT_TERM,
        integration_source=IntegrationSource.MANUAL,
        tracking_type=TrackingType.NUMERIC,
        target_value=10,
        unit="tasks"
    )
    
    with pytest.raises(ValueError, match="cannot have more than 5 active goals"):
        await repo.create_goal(goal)
