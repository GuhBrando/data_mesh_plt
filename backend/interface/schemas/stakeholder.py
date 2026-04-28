import uuid
from datetime import datetime

from pydantic import BaseModel


class StakeholderAssignModel(BaseModel):
    user_id: uuid.UUID


class StakeholderResponseModel(BaseModel):
    contract_id: uuid.UUID
    user_id: uuid.UUID
    assigned_by: uuid.UUID | None
    assigned_at: datetime
