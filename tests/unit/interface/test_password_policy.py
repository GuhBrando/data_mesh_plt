import pytest
from pydantic import ValidationError
from backend.interface.schemas.user import UserCreateModel


def test_valid_password_passes():
    m = UserCreateModel(username="Alice", email="a@b.com", password="Str0ng!Pass")
    assert m.password == "Str0ng!Pass"

def test_password_too_short_raises():
    with pytest.raises(ValidationError, match="8 characters"):
        UserCreateModel(username="Alice", email="a@b.com", password="Ab1!")

def test_password_no_uppercase_raises():
    with pytest.raises(ValidationError, match="uppercase"):
        UserCreateModel(username="Alice", email="a@b.com", password="str0ng!pass")

def test_password_no_lowercase_raises():
    with pytest.raises(ValidationError, match="lowercase"):
        UserCreateModel(username="Alice", email="a@b.com", password="STR0NG!PASS")

def test_password_no_digit_raises():
    with pytest.raises(ValidationError, match="number"):
        UserCreateModel(username="Alice", email="a@b.com", password="Strong!Pass")

def test_password_no_special_raises():
    with pytest.raises(ValidationError, match="special character"):
        UserCreateModel(username="Alice", email="a@b.com", password="Str0ngPass1")

def test_password_required():
    with pytest.raises(ValidationError):
        UserCreateModel(username="Alice", email="a@b.com")
