
from app.exceptions.exceptions import DomainError


class InvalidProjectNameError(DomainError):
    """Exception raised when project name is not provided by the client."""
    pass
class InvalidProjectDescriptionError(DomainError):
    pass

class ProjectDeletedError(DomainError):
   pass
class ProjectArchivedError(DomainError):
    pass

class InvalidProjectStateError(DomainError):
    pass