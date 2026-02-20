from pydantic import BaseModel


class UserIdentity(BaseModel):
    id: int
    name: str
    email: str
