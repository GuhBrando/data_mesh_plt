import uuid
from datetime import datetime
from typing import Any


class DataContract:
    def __init__(
        self,
        id: uuid.UUID,
        obj: dict[str, Any],
        created_at: datetime,
        updated_at: datetime,
        domain_id: uuid.UUID | None = None,
    ):
        self.id = id
        self.obj = obj
        self.created_at = created_at
        self.updated_at = updated_at
        self.domain_id = domain_id
