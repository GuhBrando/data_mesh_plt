from src.domain.user_persistence import create_user
from src.interface.schemas.user import UserCreateModel


class CreateUserInteractor:
    def __init__(self, username: str):
        self.username = username

    def execute(self):
        return create_user(
            UserCreateModel(name=self.username, email=f"{self.username}@example.com")
        )
