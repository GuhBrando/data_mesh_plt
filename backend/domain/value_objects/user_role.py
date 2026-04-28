from enum import Enum


class UserRole(str, Enum):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    DATA_OWNER = "DATA_OWNER"
    DATA_STEWARD = "DATA_STEWARD"
    DATA_CONSUMER = "DATA_CONSUMER"
