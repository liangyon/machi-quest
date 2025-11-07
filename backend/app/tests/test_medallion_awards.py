"""
Test Medallion Award System - Daily limits and multiple goals
"""
import pytest
from datetime import date
from uuid import uuid4

from app.models import User, Goal
from app.repositories.goal_repository import GoalRepository
from app.types import GoalType, TrackingType, IntegrationSource


@pytest.mark.asyncio
async def test_medallion_daily_limit(db_session):
    """Test that medallions are only awarded once per day per goal"""
    # Setup user
    user = User(id=uuid4(), email="test@example.com", medallions=0)
    db_session.add(user)
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
    created = await repo.create_goal(goal)
    
    # First award - should succeed
    updated_goal, medallions = await repo.award_medallions(created.id, user.id, amount=5)
    assert medallions == 5
    assert updated_goal.total_medallions_produced == 5
    assert updated_goal.last_completed_date == date.today()
    
    # Refresh user
    await db_session.refresh(user)
    assert user.medallions == 5
    
    # Second award same day - should fail (return 0)
    updated_goal, medallions = await repo.award_medallions(created.id, user.id, amount=5)
    assert medallions == 0  # No medallions awarded
    assert updated_goal.total_medallions_produced == 5  # Still 5, not 10
    
    # User medallions unchanged
    await db_session.refresh(user)
    assert user.medallions == 5


@pytest.mark.asyncio
async def test_multiple_goals_medallions(db_session):
    """Test that multiple goals can each award medallions"""
    # Setup
    user = User(id=uuid4(), email="test2@example.com", medallions=0)
    db_session.add(user)
    await db_session.commit()
    
    repo = GoalRepository(db_session)
    
    # Create 3 goals
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
    
    # Award medallions to all 3 goals
    total_awarded = 0
    for goal in goals:
        _, medallions = await repo.award_medallions(goal.id, user.id, amount=5)
        total_awarded += medallions
    
    assert total_awarded == 15  # 3 goals × 5 medallions
    
    # Check user total
    await db_session.refresh(user)
    assert user.medallions == 15


@pytest.mark.asyncio  
async def test_completed_goal_no_medallions(db_session):
    """Test that completed goals don't award medallions"""
    # Setup
    user = User(id=uuid4(), email="test3@example.com", medallions=0)
    db_session.add(user)
    await db_session.commit()
    
    repo = GoalRepository(db_session)
    goal = Goal(
        user_id=user.id,
        name="Test Goal",
        goal_type=GoalType.SHORT_TERM,
        integration_source=IntegrationSource.GITHUB,
        tracking_type=TrackingType.NUMERIC,
        target_value=5,
        unit="commits"
    )
    created = await repo.create_goal(goal)
    
    # Complete the goal
    for _ in range(5):
        await repo.increment_progress(created.id, amount=1)
    
    goal = await repo.get_by_id(created.id)
    assert goal.is_completed
    
    # Try to award medallions - should fail
    _, medallions = await repo.award_medallions(created.id, user.id, amount=5)
    assert medallions == 0
