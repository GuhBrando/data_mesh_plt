from src.domain.user_persistence import UserRepository
from src.infra.postgres import get_db_connection
from src.interface.schemas.user import UserCreateModel


class CreateUserInteractor:
    def __init__(self, user: UserCreateModel):
        self.user = user

    async def execute(self):
        db_connection = await get_db_connection()
        user_repository = UserRepository(db_connection)
        return await user_repository.create_user(
            UserCreateModel(
                username=self.user.username,
                email=self.user.email,
                password=self.user.password,
            )
        )
