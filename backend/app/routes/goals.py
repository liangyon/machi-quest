from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..models import User, Goal
from ..schemas.goal import (
    GoalResponse, 
    GoalCreate, 
    GoalUpdate, 
    GoalStats,
    GoalCrownRequest
)
from ..schemas.goal_template import (
    GoalTemplate,
    GoalTemplateResponse,
    CreateGoalFromTemplate,
    get_all_templates,
    get_templates_by_source,
    get_template_by_id
)
from ..types import IntegrationSource
from ..repositories.goal_repository import GoalRepository
from ..core.dependencies import get_current_user

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.get("", response_model=List[GoalResponse])
async def list_goals(
    is_completed: Optional[bool] = Query(None, description="Filter by completion status"),
    limit: Optional[int] = Query(None, le=100, description="Limit number of results"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's goals with optional filters"""
    repo = GoalRepository(db)
    goals = await repo.get_by_user_id(
        user_id=current_user.id,
        is_completed=is_completed,
        limit=limit
    )
    return goals


@router.get("/active", response_model=List[GoalResponse])
async def list_active_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's active goals (max 5)"""
    repo = GoalRepository(db)
    goals = await repo.get_active_goals(current_user.id, limit=5)
    return goals


@router.get("/stats", response_model=GoalStats)
async def get_goal_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated goal statistics for the user"""
    repo = GoalRepository(db)
    stats = await repo.get_goal_stats(current_user.id)
    return stats


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific goal details"""
    repo = GoalRepository(db)
    goal = await repo.get_by_id(goal_id)
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Verify ownership
    if goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this goal"
        )
    
    return goal


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new goal"""
    repo = GoalRepository(db)
    
    # Create goal model instance
    goal = Goal(
        user_id=current_user.id,
        name=goal_data.name,
        description=goal_data.description,
        goal_type=goal_data.goal_type,
        integration_source=goal_data.integration_source,
        integration_id=goal_data.integration_id,
        tracking_type=goal_data.tracking_type,
        target_value=goal_data.target_value,
        unit=goal_data.unit,
        visual_variant=goal_data.visual_variant,
        deadline=goal_data.deadline,
        current_progress=0,
        growth_stage=0,
        state_json={}
    )
    
    try:
        created_goal = await repo.create_goal(goal)
        return created_goal
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: str,
    goal_update: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update goal details"""
    repo = GoalRepository(db)
    goal = await repo.get_by_id(goal_id)
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Verify ownership
    if goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this goal"
        )
    
    # Update fields
    if goal_update.name is not None:
        goal.name = goal_update.name
    if goal_update.description is not None:
        goal.description = goal_update.description
    if goal_update.target_value is not None:
        goal.target_value = goal_update.target_value
    if goal_update.unit is not None:
        goal.unit = goal_update.unit
    if goal_update.visual_variant is not None:
        goal.visual_variant = goal_update.visual_variant
    if goal_update.deadline is not None:
        goal.deadline = goal_update.deadline
    if goal_update.is_completed is not None:
        goal.is_completed = goal_update.is_completed
    
    updated_goal = await repo.update(goal)
    return updated_goal


@router.post("/{goal_id}/crown", response_model=GoalResponse)
async def crown_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually crown a goal (for short-term goals that reached their target)"""
    repo = GoalRepository(db)
    goal = await repo.get_by_id(goal_id)
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Verify ownership
    if goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to crown this goal"
        )
    
    # Crown the goal
    crowned_goal = await repo.mark_crowned(goal_id)
    return crowned_goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a goal (marks as completed)"""
    repo = GoalRepository(db)
    goal = await repo.get_by_id(goal_id)
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Verify ownership
    if goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this goal"
        )
    
    await repo.soft_delete(goal_id)
    return None


# Goal Template Endpoints

@router.get("/templates/all", response_model=GoalTemplateResponse)
async def list_all_templates(
    current_user: User = Depends(get_current_user)
):
    """Get all available goal templates"""
    templates = get_all_templates()
    return GoalTemplateResponse(
        templates=templates,
        count=len(templates)
    )


@router.get("/templates/{integration_source}", response_model=GoalTemplateResponse)
async def list_templates_by_source(
    integration_source: IntegrationSource,
    current_user: User = Depends(get_current_user)
):
    """Get goal templates for a specific integration source (github, strava, manual)"""
    templates = get_templates_by_source(integration_source)
    return GoalTemplateResponse(
        templates=templates,
        count=len(templates)
    )


@router.post("/from-template", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal_from_template(
    request: CreateGoalFromTemplate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a goal from a predefined template"""
    # Get the template
    template = get_template_by_id(request.template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template not found: {request.template_id}"
        )
    
    # Use template values, with optional overrides
    goal_name = request.name if request.name else template.name
    target_value = request.target_value if request.target_value else template.target_value
    
    # Create goal from template
    repo = GoalRepository(db)
    goal = Goal(
        user_id=current_user.id,
        name=goal_name,
        description=template.description,
        goal_type=template.goal_type,
        integration_source=template.integration_source,
        integration_id=None,  # Will be set if user has integration
        tracking_type=template.tracking_type,
        target_value=target_value,
        unit=template.unit,
        visual_variant=template.visual_variant,
        deadline=None,  # User can set later
        current_progress=0,
        growth_stage=0,
        state_json={}
    )
    
    try:
        created_goal = await repo.create_goal(goal)
        return created_goal
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
