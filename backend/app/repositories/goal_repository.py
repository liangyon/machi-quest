from typing import List, Optional
from uuid import UUID
from datetime import date, datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository
from ..models import Goal, User


class GoalRepository(BaseRepository[Goal]):
    def __init__(self, db: AsyncSession):
        super().__init__(Goal, db)

    async def get_by_user_id(
        self, 
        user_id: UUID, 
        is_completed: Optional[bool] = None,
        limit: Optional[int] = None
    ) -> List[Goal]:
        """Get goals for a user with optional filters"""
        query = select(self.model).where(self.model.user_id == user_id)
        
        if is_completed is not None:
            query = query.where(self.model.is_completed == is_completed)
        
        query = query.order_by(self.model.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_goals(self, user_id: UUID, limit: int = 5) -> List[Goal]:
        """Get active (not completed) goals for a user"""
        return await self.get_by_user_id(user_id, is_completed=False, limit=limit)

    async def count_active_goals(self, user_id: UUID) -> int:
        """Count active goals for a user"""
        result = await self.db.execute(
            select(func.count(self.model.id)).where(
                and_(
                    self.model.user_id == user_id,
                    self.model.is_completed == False
                )
            )
        )
        return result.scalar_one()

    async def get_by_integration(
        self, 
        user_id: UUID, 
        integration_source: str
    ) -> List[Goal]:
        """Get all active goals for a specific integration source"""
        result = await self.db.execute(
            select(self.model).where(
                and_(
                    self.model.user_id == user_id,
                    self.model.integration_source == integration_source,
                    self.model.is_completed == False
                )
            )
        )
        return list(result.scalars().all())

    async def create_goal(self, goal: Goal) -> Goal:
        """Create a new goal with validation"""
        # Check if user already has 5 active goals
        active_count = await self.count_active_goals(goal.user_id)
        if active_count >= 5:
            raise ValueError("User cannot have more than 5 active goals")
        
        return await self.create(goal)

    async def increment_progress(
        self, 
        goal_id: UUID, 
        amount: int = 1
    ) -> Optional[Goal]:
        """Increment goal progress and update growth stage"""
        goal = await self.get_by_id(goal_id)
        if not goal or goal.is_completed:
            return goal
        
        # Increment progress
        goal.current_progress += amount
        
        # Update growth stage based on progress percentage
        progress_pct = (goal.current_progress / goal.target_value) * 100
        if progress_pct >= 100:
            goal.growth_stage = 3  # Crowned
            goal.is_crowned = True
            if not goal.completed_at:
                goal.completed_at = datetime.utcnow()
                goal.is_completed = True
        elif progress_pct >= 66:
            goal.growth_stage = 2  # Adult
        elif progress_pct >= 33:
            goal.growth_stage = 1  # Teen
        else:
            goal.growth_stage = 0  # Baby
        
        return await self.update(goal)

    async def can_award_medallions_today(self, goal_id: UUID) -> bool:
        """Check if medallions can be awarded today (max 5 per goal per day)"""
        goal = await self.get_by_id(goal_id)
        if not goal:
            return False
        
        # Check if last completion was today
        today = date.today()
        if goal.last_completed_date == today:
            # Already awarded today, cannot award more
            return False
        
        return True

    async def award_medallions(
        self, 
        goal_id: UUID, 
        user_id: UUID, 
        amount: int = 5
    ) -> tuple[Optional[Goal], int]:
        """
        Award medallions for goal progress.
        Returns (updated_goal, medallions_awarded)
        """
        # Check if can award today
        if not await self.can_award_medallions_today(goal_id):
            return await self.get_by_id(goal_id), 0
        
        goal = await self.get_by_id(goal_id)
        if not goal:
            return None, 0
        
        # Update goal medallion tracking
        goal.total_medallions_produced += amount
        goal.last_completed_date = date.today()
        
        # Update user medallions
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            user.medallions += amount
        
        await self.update(goal)
        
        return goal, amount

    async def mark_crowned(self, goal_id: UUID) -> Optional[Goal]:
        """Manually mark a goal as crowned (for short-term goals)"""
        goal = await self.get_by_id(goal_id)
        if not goal:
            return None
        
        goal.is_crowned = True
        goal.growth_stage = 3
        if not goal.completed_at:
            goal.completed_at = datetime.utcnow()
            goal.is_completed = True
        
        return await self.update(goal)

    async def get_completed_today(self, user_id: UUID) -> List[Goal]:
        """Get goals that were completed today"""
        today = date.today()
        result = await self.db.execute(
            select(self.model).where(
                and_(
                    self.model.user_id == user_id,
                    self.model.last_completed_date == today
                )
            )
        )
        return list(result.scalars().all())

    async def get_goal_stats(self, user_id: UUID) -> dict:
        """Get aggregated statistics for user's goals"""
        all_goals = await self.get_by_user_id(user_id)
        
        total_goals = len(all_goals)
        active_goals = len([g for g in all_goals if not g.is_completed])
        completed_goals = len([g for g in all_goals if g.is_completed])
        crowned_goals = len([g for g in all_goals if g.is_crowned])
        total_medallions = sum(g.total_medallions_produced for g in all_goals)
        
        # Calculate completion rate
        completion_rate = (completed_goals / total_goals * 100) if total_goals > 0 else 0.0
        
        return {
            "total_goals": total_goals,
            "active_goals": active_goals,
            "completed_goals": completed_goals,
            "crowned_goals": crowned_goals,
            "total_medallions_earned": total_medallions,
            "average_completion_rate": completion_rate,
            "longest_streak": 0,  # TODO: Implement streak tracking
            "current_streak": 0   # TODO: Implement streak tracking
        }

    async def soft_delete(self, goal_id: UUID) -> Optional[Goal]:
        """Soft delete a goal by marking it as completed"""
        goal = await self.get_by_id(goal_id)
        if not goal:
            return None
        
        goal.is_completed = True
        goal.completed_at = datetime.utcnow()
        
        return await self.update(goal)
