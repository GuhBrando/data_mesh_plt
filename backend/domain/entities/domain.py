import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DomainMember:
    user_id: uuid.UUID
    username: str
    role: str  # 'maintainer' | 'member'


class Domain:
    def __init__(
        self,
        id: uuid.UUID,
        name: str,
        description: str = "",
        owner_id: uuid.UUID | None = None,
        owner_username: str = "",
        members: list | None = None,
        contract_count: int = 0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.owner_id = owner_id
        self.owner_username = owner_username
        self.members: list[DomainMember] = members if members is not None else []
        self.contract_count = contract_count
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return f"Domain(id={self.id}, name={self.name})"
