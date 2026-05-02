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


# ── ChangePasswordModel validator ────────────────────────────────────────────

from backend.interface.schemas.user import ChangePasswordModel


def test_change_password_valid():
    m = ChangePasswordModel(current_password="OldPass1!", new_password="NewStr0ng!")
    assert m.new_password == "NewStr0ng!"


def test_change_password_too_short():
    with pytest.raises(ValidationError, match="8 characters"):
        ChangePasswordModel(current_password="old", new_password="Ab1!")


def test_change_password_no_uppercase():
    with pytest.raises(ValidationError, match="uppercase"):
        ChangePasswordModel(current_password="old", new_password="newstr0ng!")


def test_change_password_no_lowercase():
    with pytest.raises(ValidationError, match="lowercase"):
        ChangePasswordModel(current_password="old", new_password="NEWSTR0NG!")


def test_change_password_no_digit():
    with pytest.raises(ValidationError, match="number"):
        ChangePasswordModel(current_password="old", new_password="NewStrong!")


def test_change_password_no_special():
    with pytest.raises(ValidationError, match="special character"):
        ChangePasswordModel(current_password="old", new_password="NewStr0ng1")
