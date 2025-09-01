from typing import Any
from pydantic import EmailStr
from sqlalchemy import or_, select, update, delete as delete_query
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User, Task, Habit, Tag 
from src.schemas.user_dto import UserCreate, UserUpdate
from src.security.password_hashing import hash_password


class UserRepository:
    """
    Class repository for all operations with the User model in the database.
    Encapsulates all logic for database queries.
    """

    # --- CREATION METHODS ---
    
    async def create(self, db: AsyncSession, user_in: UserCreate) -> User:
        """Создает нового пользователя в базе данных."""
        user = User(
            username=user_in.username,
            email=user_in.email,
            # Correct the field name to match the one in the model: hash_password
            password_in_hash=hash_password(user_in.password),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    # --- READING METHODS (GET) ---

    async def select_by_id(self, db: AsyncSession, user_id: int) -> User | None:
        """Получает пользователя по ID (легкая версия)."""
        return await self._get_by_attribute(db, "id", user_id)

    async def select_by_username(self, db: AsyncSession, username: str) -> User | None:
        """Получает пользователя по имени пользователя."""
        return await self._get_by_attribute(db, "username", username)

    async def select_by_email(self, db: AsyncSession, email: EmailStr) -> User | None:
        """Получает пользователя по email."""
        return await self._get_by_attribute(db, "email", email)
    
    async def select_by_username_or_email(self, db: AsyncSession, username: str, email: str) -> User | None:
        """Получает пользователя по имени ИЛИ по email (для проверки при регистрации)."""
        query = select(User).filter(or_(User.username == username, User.email == email))
        result = await db.execute(query)
        return result.scalar_one_or_none()
    

    async def select_with_tasks(self, db: AsyncSession, user_id: int) -> User | None:
        return await self._get_by_attribute_with_relation(db, "id", user_id, "tasks")

    async def select_with_habits(self, db: AsyncSession, user_id: int) -> User | None:
        return await self._get_by_attribute_with_relation(db, "id", user_id, "habits")

    async def select_with_tags(self, db: AsyncSession, user_id: int) -> User | None:
        return await self._get_by_attribute_with_relation(db, "id", user_id, "tags")

    async def select_with_all_relations(self, db: AsyncSession, user_id: int) -> User | None:
        """Retrieves a user with all their primary relationships (heavy version)."""
        query = (
            select(User)
            .filter(User.id == user_id)
            .options(
                selectinload(User.tasks).selectinload(Task.tags), # We load tasks and tags for each task.
                selectinload(User.habits),
                selectinload(User.tags) 
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    # --- UPDATE METHODS ---

    async def update(self, db: AsyncSession, user_to_update: User, new_data: UserUpdate) -> User:
        """Updates user data (except for the password)."""
        data = new_data.model_dump(exclude_unset=True)
        if not data:
            return user_to_update
        
        query = (
            update(User)
            .filter(User.id == user_to_update.id)
            .values(**data)
            .returning(User)
        )
        result = await db.execute(query)
        await db.commit()
        return result.scalar_one()
    
    # --- REMOVAL METHODS ---

    async def delete(self, db: AsyncSession, user_to_delete: User) -> None:
        """Removes the user from the database."""
        await db.delete(user_to_delete) 
        await db.commit()
    
    # --- INTERNAL (PRIVATE) METHODS ---
    
    async def _get_by_attribute(self, db: AsyncSession, attribute: str, value: Any) -> User | None:
        """Internal universal method for searching for a user by a single attribute."""
        query = select(User).filter(getattr(User, attribute) == value)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_by_attribute_with_relation(self, db: AsyncSession, attribute: str, value: Any, relation: str) -> User | None:
        """internal universal method for loading a user with a relationship."""
        query = (
            select(User)
            .filter(getattr(User, attribute) == value)
            .options(selectinload(getattr(User, relation)))
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()


user_repo = UserRepository()