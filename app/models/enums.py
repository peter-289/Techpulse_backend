from enum import Enum

# Gender Enum
class GenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    NON_BINARY = "NON_BINARY"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY"

class UserStatus(str, Enum):
    UNAPROVED = "UNAPPROVED"
    VERIFIED = "VERIFIED"
    SUSPENDED = "SUSPENDED"  

class RoleEnum(str, Enum): 
    ADMIN = "ADMIN"
    USER = "USER"