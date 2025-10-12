"""기본 도메인 예외."""


class DomainException(Exception):
    """도메인 레이어의 기본 예외."""

    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ModelNotLoadedError(DomainException):
    """모델이 로드되지 않았을 때 발생합니다."""

    def __init__(self, message: str = "모델이 로드되지 않았습니다"):
        super().__init__(message, code="MODEL_NOT_LOADED")


class InferenceError(DomainException):
    """추론이 실패했을 때 발생합니다."""

    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message, code="INFERENCE_ERROR")
        self.original_error = original_error


class InvalidImageError(DomainException):
    """이미지가 유효하지 않을 때 발생합니다."""

    def __init__(self, message: str):
        super().__init__(message, code="INVALID_IMAGE")