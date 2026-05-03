import uuid
from datetime import datetime

from pydantic import BaseModel


class DomainCreateModel(BaseModel):
    name: str
    description: str = ""
    owner_id: uuid.UUID | None = None


class DomainUpdateModel(BaseModel):
    name: str | None = None
    description: str | None = None
    owner_id: uuid.UUID | None = None


class DomainMemberResponse(BaseModel):
    user_id: uuid.UUID
    username: str
    role: str


class DomainWithMembersResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    owner_id: uuid.UUID | None
    owner_username: str
    members: list[DomainMemberResponse]
    contract_count: int
    created_at: datetime
    updated_at: datetime


class DomainAddMemberModel(BaseModel):
    user_id: uuid.UUID
    role: str = "member"


class DomainUpdateMemberModel(BaseModel):
    role: str


# Legacy — kept for backward compatibility
class DomainMemberModel(BaseModel):
    user_id: uuid.UUID


class RoleAssignModel(BaseModel):
    role: str
