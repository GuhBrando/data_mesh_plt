import uuid

from backend.domain.value_objects.email import Email


class User:
    def __init__(self, id: uuid.UUID, name: str, email: Email, password_hash: str = ""):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash

    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, email={self.email})"
