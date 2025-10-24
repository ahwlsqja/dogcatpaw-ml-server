"""gRPC Servicer 구현."""
import logging
from typing import Protocol

# 참고: 이것들은 proto 파일에서 생성될 것입니다
# import nose_embedder_pb2
# import nose_embedder_pb2_grpc

from ...application.use_cases import (
    ExtractEmbeddingUseCase,
    HealthCheckUseCase,
)
from ...application.use_cases.compare_with_stored_image import (
    CompareWithStoredImageUseCase,
)
from ...domain.exceptions import (
    DomainException,
    ModelNotLoadedError,
    InferenceError,
    InvalidImageError,
    ImageTooLargeError,
    InvalidImageFormatError,
    VectorNotFoundError,
    VectorDimensionMismatchError,
    InvalidRequestError,
    StorageConnectionError,
    InternalServerError,
    ServiceUnavailableError,
    get_proto_error_code,
)

logger = logging.getLogger(__name__)


class NoseEmbedderServicer:
    """
    Nose Embedder 서비스를 위한 gRPC Servicer.

    gRPC 요청을 유스케이스 실행으로 변환하는 어댑터 레이어입니다.
    """

    def __init__(
        self,
        extract_embedding_use_case: ExtractEmbeddingUseCase,
        health_check_use_case: HealthCheckUseCase,
        compare_with_stored_image_use_case: CompareWithStoredImageUseCase,
    ):
        """
        Servicer를 초기화합니다.

        Args:
            extract_embedding_use_case: 임베딩 추출을 위한 유스케이스
            health_check_use_case: 헬스 체크를 위한 유스케이스
            compare_with_stored_image_use_case: 저장된 이미지와 비교를 위한 유스케이스
        """
        self._extract_embedding = extract_embedding_use_case
        self._health_check = health_check_use_case
        self._compare_with_stored_image = compare_with_stored_image_use_case

    async def ExtractNoseVector(self, request, context):
        """
        코 이미지에서 임베딩을 추출합니다.

        Args:
            request: NoseImageRequest
            context: gRPC 컨텍스트

        Returns:
            NoseVectorResponse
        """
        logger.info(f"ExtractNoseVector 요청 수신 (크기: {len(request.image_data)} bytes)")

        try:
            # 유스케이스 실행
            embedding = await self._extract_embedding.execute(
                image_data=request.image_data,
                image_format=request.image_format if request.image_format else None
            )

            # 순환 의존성을 피하기 위해 여기서 import
            import nose_embedder_pb2

            # 성공 응답 반환
            return nose_embedder_pb2.NoseVectorResponse(
                vector=embedding.vector,
                vector_size=embedding.dimension,
                success=True,
                error_message=""
            )

        except DomainException as e:
            # 도메인 예외 - 에러 코드와 재시도 정보 포함
            logger.error(f"도메인 에러: [{e.code}] {e.message}")

            import nose_embedder_pb2
            return nose_embedder_pb2.NoseVectorResponse(
                success=False,
                error_message=e.message,
                error_code=get_proto_error_code(e.code),
                retryable=e.retryable
            )

        except Exception as e:
            # 예상치 못한 에러 - INTERNAL_SERVER_ERROR로 처리
            logger.exception(f"예상치 못한 에러: {e}")

            import nose_embedder_pb2
            return nose_embedder_pb2.NoseVectorResponse(
                success=False,
                error_message=f"내부 에러: {str(e)}",
                error_code=get_proto_error_code("ML_5004"),  # INTERNAL_SERVER_ERROR
                retryable=True
            )

    async def HealthCheck(self, request, context):
        """
        헬스 체크를 수행합니다.

        Args:
            request: HealthCheckRequest
            context: gRPC 컨텍스트

        Returns:
            HealthCheckResponse
        """
        logger.debug("HealthCheck 요청 수신")

        try:
            # 유스케이스 실행
            status = await self._health_check.execute()

            import nose_embedder_pb2

            # 상태 문자열을 enum으로 매핑
            status_enum = (
                nose_embedder_pb2.HealthCheckResponse.SERVING
                if status["model_loaded"]
                else nose_embedder_pb2.HealthCheckResponse.NOT_SERVING
            )

            model_info = status.get("model_info", {})
            message = f"모델: {model_info.get('model_path', 'N/A')}"

            return nose_embedder_pb2.HealthCheckResponse(
                status=status_enum,
                message=message,
                model_loaded="로드됨 (ONNX)" if status["model_loaded"] else "로드되지 않음",
                timestamp=status["timestamp"]
            )

        except Exception as e:
            logger.exception(f"헬스 체크 실패: {e}")

            import nose_embedder_pb2

            return nose_embedder_pb2.HealthCheckResponse(
                status=nose_embedder_pb2.HealthCheckResponse.NOT_SERVING,
                message=f"에러: {str(e)}",
                model_loaded="에러",
                timestamp=""
            )

    async def CompareWithStoredImage(self, request, context):
        """
        NCP에 저장된 이미지를 저장된 벡터와 비교합니다.

        Args:
            request: CompareWithStoredImageRequest
            context: gRPC 컨텍스트

        Returns:
            CompareVectorsResponse
        """
        logger.info(
            f"CompareWithStoredImage 요청 수신: "
            f"image_key={request.image_key}, "
            f"pet_did={request.pet_did}"
        )

        try:
            # 유스케이스 실행
            similarity_result = await self._compare_with_stored_image.execute(
                image_key=request.image_key,
                pet_did=request.pet_did,
            )

            import nose_embedder_pb2

            # 성공 응답 반환
            return nose_embedder_pb2.CompareVectorsResponse(
                similarity=similarity_result.similarity,
                cosine_similarity=similarity_result.cosine_similarity,
                euclidean_distance=similarity_result.euclidean_distance,
                vector_size=similarity_result.vector_size,
                success=True,
                error_message=""
            )

        except DomainException as e:
            # 도메인 예외 - 에러 코드와 재시도 정보 포함
            logger.error(f"도메인 에러: [{e.code}] {e.message}")

            import nose_embedder_pb2
            return nose_embedder_pb2.CompareVectorsResponse(
                success=False,
                error_message=e.message,
                error_code=get_proto_error_code(e.code),
                retryable=e.retryable
            )

        except Exception as e:
            # 예상치 못한 에러 - INTERNAL_SERVER_ERROR로 처리
            logger.exception(f"예상치 못한 에러: {e}")

            import nose_embedder_pb2
            return nose_embedder_pb2.CompareVectorsResponse(
                success=False,
                error_message=f"내부 에러: {str(e)}",
                error_code=get_proto_error_code("ML_5004"),  # INTERNAL_SERVER_ERROR
                retryable=True
            )