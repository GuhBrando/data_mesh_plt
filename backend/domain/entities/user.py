import uuid

from backend.domain.value_objects.email import Email


class User:
    """
    Entity representing a user.
    """

    def __init__(self, id: uuid.UUID, name: str, email: Email):
        self.id = id
        self.name = name
        self.email = email

    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, email={self.email})"
