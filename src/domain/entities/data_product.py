import uuid
from datetime import datetime


class DataProduct:
    def __init__(
        self,
        id: uuid.UUID,
        name: str,
        description: str,
        data_contracts_id: uuid.UUID,
        created_at: datetime,
        updated_at: datetime,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.data_contracts_id = data_contracts_id
        self.created_at = created_at
        self.updated_at = updated_at
