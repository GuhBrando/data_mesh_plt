from pydantic import BaseModel

class UserCreateModel(BaseModel):
    """
    Represents the data required to create a new user.

    Attributes:
        username (str): The username of the user.
        email (str): The email address of the user.
        password (str): The password for the user account.
    """
    username: str
    email: str
    password: str


class UserResponseModel(BaseModel):
    """
    Represents the data returned as a response for user-related operations.

    Attributes:
        id (int): The unique identifier of the user.
        username (str): The username of the user.
        email (str): The email address of the user.
    """
    id: int
    username: str
    email: str


class UserIdentity(BaseModel):
    """
    Represents the identity details of a user.

    Attributes:
        id (int): The unique identifier of the user.
        name (str): The name of the user.
        email (str): The email address of the user.
    """
    id: int
    name: str
    email: str
