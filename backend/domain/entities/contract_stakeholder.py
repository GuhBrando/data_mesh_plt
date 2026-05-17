import uuid
from datetime import datetime


class ContractStakeholder:
    def __init__(
        self,
        contract_id: uuid.UUID,
        user_id: uuid.UUID,
        assigned_by: uuid.UUID | None,
        assigned_at: datetime,
    ):
        self.contract_id = contract_id
        self.user_id = user_id
        self.assigned_by = assigned_by
        self.assigned_at = assigned_at
