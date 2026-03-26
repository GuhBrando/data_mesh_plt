from typing import List

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.interface.schemas.user import UserCreateModel, UserUpdateModel


class UserRepository:
    """
    Repository for managing user entities.
    """

    def __init__(self, db_connection):
        self.db_connection = db_connection

    async def create_user(self, user_data: UserCreateModel) -> User:
        """Creates a new user in the database."""
        async with self.db_connection.transaction():
            result = await self.db_connection.fetchrow(
                """
                INSERT INTO users (username, email)
                VALUES ($1, $2)
                RETURNING id, name, email;
                """,
                user_data.username,
                user_data.email,
            )
            return User(
                id=result["id"], name=result["name"], email=Email(result["email"])
            )

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Fetches a user by ID."""
        result = await self.db_connection.fetchrow(
            "SELECT id, name, email FROM users WHERE id = $1;",
            user_id,
        )
        if result:
            return User(
                id=result["id"], name=result["name"], email=Email(result["email"])
            )
        return None

    async def list_users(self) -> List[User]:
        """Lists all users."""
        results = await self.db_connection.fetch("SELECT id, name, email FROM users;")
        return [
            User(id=row["id"], name=row["name"], email=Email(row["email"]))
            for row in results
        ]

    async def update_user(
        self, user_id: int, user_data: UserUpdateModel
    ) -> User | None:
        """Updates user data."""
        async with self.db_connection.transaction():
            result = await self.db_connection.fetchrow(
                """
                UPDATE users
                SET name = $1, email = $2
                WHERE id = $3
                RETURNING id, name, email;
                """,
                user_data.name,
                user_data.email,
                user_id,
            )
            if result:
                return User(
                    id=result["id"], name=result["name"], email=Email(result["email"])
                )
            return None
