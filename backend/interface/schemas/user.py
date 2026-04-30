import re
import uuid

from pydantic import BaseModel, field_validator


class UserCreateModel(BaseModel):
    username: str
    email: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError(
                "Password must contain at least one special character (!@#$%^&*)"
            )
        return v


class UserResponseModel(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    role: str


class UserUpdateModel(BaseModel):
    username: str | None = None
    email: str | None = None


class ChangePasswordModel(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError(
                "Password must contain at least one special character (!@#$%^&*)"
            )
        return v


class UserIdentity(BaseModel):
    id: uuid.UUID
    name: str
    email: str
