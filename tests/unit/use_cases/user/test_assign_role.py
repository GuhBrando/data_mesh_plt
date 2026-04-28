import uuid
from backend.domain.entities.user import User
from backend.domain.value_objects.email import Email
from backend.domain.value_objects.user_role import UserRole


def test_user_defaults_to_data_consumer():
    user = User(id=uuid.uuid4(), name="Alice", email=Email("alice@example.com"))
    assert user.role == UserRole.DATA_CONSUMER


def test_user_can_be_created_with_explicit_role():
    user = User(
        id=uuid.uuid4(),
        name="Bob",
        email=Email("bob@example.com"),
        role=UserRole.PLATFORM_ADMIN,
    )
    assert user.role == UserRole.PLATFORM_ADMIN
