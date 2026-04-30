import uuid

from backend.domain.value_objects.email import Email
from backend.domain.value_objects.user_role import UserRole


class User:
    def __init__(
        self,
        id: uuid.UUID,
        name: str,
        email: Email,
        password_hash: str = "",
        role: UserRole = UserRole.DATA_CONSUMER,
    ):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.role = role

    def __repr__(self):
        return (
            f"User(id={self.id}, name={self.name}, "
            f"email={self.email}, role={self.role})"
        )
