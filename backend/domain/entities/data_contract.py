import uuid
from datetime import datetime
from typing import Any


class DataContract:
    def __init__(
        self,
        id: uuid.UUID,
        title: str,
        version: str,
        owner: str,
        domain: str,
        tier: int,
        status: str,
        models: dict[str, Any],
        servicelevels: dict[str, Any],
        created_at: datetime,
        updated_at: datetime,
        domain_id: uuid.UUID | None = None,
    ):
        self.id = id
        self.title = title
        self.version = version
        self.owner = owner
        self.domain = domain
        self.tier = tier
        self.status = status
        self.models = models
        self.servicelevels = servicelevels
        self.created_at = created_at
        self.updated_at = updated_at
        self.domain_id = domain_id
