class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, resource: str, id: int):
        super().__init__(f"{resource} {id} not found", status_code=404)


class ConflictError(AppError):
    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)
