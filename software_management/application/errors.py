class ApplicationError(Exception):
    pass


class NotFoundError(ApplicationError):
    pass


class ConflictError(ApplicationError):
    pass


class ForbiddenError(ApplicationError):
    pass


class ValidationError(ApplicationError):
    pass

