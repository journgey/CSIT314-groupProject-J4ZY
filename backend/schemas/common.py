from enum import Enum

class AccountRole(str, Enum):
    UserAdmin = "UserAdmin"
    CSR = "CSR"
    PIN = "PIN"
    PlatformManager = "PlatformManager"

class AccountStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    blocked = "blocked"

class RequestStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    completed = "completed"
    expired = "expired"
