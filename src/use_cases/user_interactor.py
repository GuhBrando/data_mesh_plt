from src.domain.user_persistence import User, create_user


class CreateUserInteractor:
    def __init__(self, username: str):
        self.username = username

    def execute(self):
        return create_user(
            User(name=self.username, email=f"{self.username}@example.com")
        )
