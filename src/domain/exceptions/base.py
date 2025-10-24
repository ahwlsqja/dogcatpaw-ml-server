"""기본 도메인 예외."""


class DomainException(Exception):
    """도메인 레이어의 기본 예외."""

    def __init__(self, message: str, code: str = "DOMAIN_ERROR", retryable: bool = False):
        self.message = message
        self.code = code
        self.retryable = retryable
        super().__init__(self.message)


# ============================================
# 4xxx: 재시도 불가능한 클라이언트 에러
# ============================================

class InvalidImageError(DomainException):
    """이미지가 유효하지 않을 때 발생합니다. (ML_4001)"""

    def __init__(self, message: str = "유효하지 않은 이미지입니다"):
        super().__init__(message, code="ML_4001", retryable=False)


class ImageTooLargeError(DomainException):
    """이미지 크기가 너무 클 때 발생합니다. (ML_4002)"""

    def __init__(self, message: str = "이미지 크기가 너무 큽니다"):
        super().__init__(message, code="ML_4002", retryable=False)


class InvalidImageFormatError(DomainException):
    """지원하지 않는 이미지 형식일 때 발생합니다. (ML_4003)"""

    def __init__(self, message: str = "지원하지 않는 이미지 형식입니다"):
        super().__init__(message, code="ML_4003", retryable=False)


class VectorNotFoundError(DomainException):
    """저장된 벡터를 찾을 수 없을 때 발생합니다. (ML_4004)"""

    def __init__(self, message: str = "저장된 벡터를 찾을 수 없습니다"):
        super().__init__(message, code="ML_4004", retryable=False)


class VectorDimensionMismatchError(DomainException):
    """벡터 차원이 일치하지 않을 때 발생합니다. (ML_4005)"""

    def __init__(self, message: str = "벡터 차원이 일치하지 않습니다"):
        super().__init__(message, code="ML_4005", retryable=False)


class InvalidRequestError(DomainException):
    """잘못된 요청 파라미터일 때 발생합니다. (ML_4006)"""

    def __init__(self, message: str = "잘못된 요청입니다"):
        super().__init__(message, code="ML_4006", retryable=False)


# ============================================
# 5xxx: 재시도 가능한 서버 에러
# ============================================

class ModelNotLoadedError(DomainException):
    """모델이 로드되지 않았을 때 발생합니다. (ML_5001)"""

    def __init__(self, message: str = "ML 모델이 로드되지 않았습니다"):
        super().__init__(message, code="ML_5001", retryable=True)


class InferenceError(DomainException):
    """추론이 실패했을 때 발생합니다. (ML_5002)"""

    def __init__(self, message: str = "추론 중 오류가 발생했습니다", original_error: Exception = None):
        super().__init__(message, code="ML_5002", retryable=True)
        self.original_error = original_error


class StorageConnectionError(DomainException):
    """스토리지 연결에 실패했을 때 발생합니다. (ML_5003)"""

    def __init__(self, message: str = "스토리지 연결에 실패했습니다"):
        super().__init__(message, code="ML_5003", retryable=True)


class InternalServerError(DomainException):
    """내부 서버 오류가 발생했을 때 발생합니다. (ML_5004)"""

    def __init__(self, message: str = "ML 서버 내부 오류가 발생했습니다"):
        super().__init__(message, code="ML_5004", retryable=True)


class ServiceUnavailableError(DomainException):
    """서비스를 일시적으로 사용할 수 없을 때 발생합니다. (ML_5005)"""

    def __init__(self, message: str = "ML 서비스를 일시적으로 사용할 수 없습니다"):
        super().__init__(message, code="ML_5005", retryable=True)


# ============================================
# 에러 코드 매핑 (Proto enum과 매핑)
# ============================================

ERROR_CODE_TO_PROTO_ENUM = {
    "ML_4001": 0,  # INVALID_IMAGE
    "ML_4002": 1,  # IMAGE_TOO_LARGE
    "ML_4003": 2,  # INVALID_IMAGE_FORMAT
    "ML_4004": 3,  # VECTOR_NOT_FOUND
    "ML_4005": 4,  # VECTOR_DIMENSION_MISMATCH
    "ML_4006": 5,  # INVALID_REQUEST
    "ML_5001": 6,  # MODEL_NOT_LOADED
    "ML_5002": 7,  # INFERENCE_ERROR
    "ML_5003": 8,  # STORAGE_CONNECTION_ERROR
    "ML_5004": 9,  # INTERNAL_SERVER_ERROR
    "ML_5005": 10, # SERVICE_UNAVAILABLE
}


def get_proto_error_code(error_code: str) -> int:
    """에러 코드를 Proto enum 값으로 변환합니다."""
    return ERROR_CODE_TO_PROTO_ENUM.get(error_code, 9)  # 기본값: INTERNAL_SERVER_ERROR