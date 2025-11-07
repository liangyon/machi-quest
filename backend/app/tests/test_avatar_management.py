"""
Test Avatar CRUD Operations
"""
import pytest
from uuid import uuid4

from app.models import User, Avatar
from app.repositories.avatar_repository import AvatarRepository


@pytest.mark.asyncio
async def test_create_avatar(db_session):
    """Test creating an avatar for a user"""
    # Create user
    user = User(id=uuid4(), email="test@example.com", medallions=0)
    db_session.add(user)
    await db_session.commit()
    
    # Create avatar
    repo = AvatarRepository(db_session)
    avatar = await repo.create_default_avatar(user.id, species="cat")
    
    assert avatar.id is not None
    assert avatar.user_id == user.id
    assert avatar.species == "cat"
    assert avatar.customization_json == {}
    assert avatar.state_json == {}


@pytest.mark.asyncio
async def test_get_or_create_avatar(db_session):
    """Test get_or_create ensures one avatar per user"""
    user = User(id=uuid4(), email="test2@example.com", medallions=0)
    db_session.add(user)
    await db_session.commit()
    
    repo = AvatarRepository(db_session)
    
    # First call - creates avatar
    avatar1 = await repo.get_or_create_avatar(user.id, species="default")
    assert avatar1 is not None
    avatar1_id = avatar1.id
    
    # Second call - returns existing
    avatar2 = await repo.get_or_create_avatar(user.id, species="cat")
    assert avatar2.id == avatar1_id
    assert avatar2.species == "default"  # Species not changed


@pytest.mark.asyncio
async def test_update_avatar_customization(db_session):
    """Test updating avatar customization"""
    user = User(id=uuid4(), email="test3@example.com", medallions=0)
    db_session.add(user)
    await db_session.commit()
    
    repo = AvatarRepository(db_session)
    avatar = await repo.create_default_avatar(user.id)
    
    # Update customization
    custom_data = {"color": "blue", "accessories": ["hat", "glasses"]}
    updated = await repo.update_customization(avatar.id, custom_data)
    
    assert updated.customization_json == custom_data
    
    # Verify persistence
    fetched = await repo.get_by_id(avatar.id)
    assert fetched.customization_json == custom_data


@pytest.mark.asyncio
async def test_update_avatar_species(db_session):
    """Test changing avatar species"""
    user = User(id=uuid4(), email="test4@example.com", medallions=0)
    db_session.add(user)
    await db_session.commit()
    
    repo = AvatarRepository(db_session)
    avatar = await repo.create_default_avatar(user.id, species="default")
    
    # Change species
    updated = await repo.update_species(avatar.id, "cat")
    assert updated.species == "cat"
    
    # Verify
    fetched = await repo.get_by_id(avatar.id)
    assert fetched.species == "cat"
