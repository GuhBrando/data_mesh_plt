import uuid

from pydantic import BaseModel


class DomainCreateModel(BaseModel):
    name: str


class DomainResponseModel(BaseModel):
    id: uuid.UUID
    name: str


class DomainMemberModel(BaseModel):
    user_id: uuid.UUID


class RoleAssignModel(BaseModel):
    role: str
