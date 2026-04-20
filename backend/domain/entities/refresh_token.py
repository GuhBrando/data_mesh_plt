import uuid
from datetime import datetime


class RefreshToken:
    def __init__(
        self,
        id: uuid.UUID,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        revoked: bool,
    ):
        self.id = id
        self.user_id = user_id
        self.token_hash = token_hash
        self.expires_at = expires_at
        self.revoked = revoked
