"""임베딩 추출 유스케이스."""
import logging
from typing import Protocol

from ...domain.entities.embedding import Embedding
from ...domain.entities.nose_image import NoseImage
from ...domain.repositories.model_repository import ModelRepository
from ...domain.exceptions import InvalidImageError

logger = logging.getLogger(__name__)


class ExtractEmbeddingUseCase:
    """
    코 이미지에서 임베딩을 추출하는 유스케이스.

    전달 메커니즘(gRPC, REST 등)과 독립적인
    임베딩 추출을 위한 비즈니스 로직을 캡슐화합니다.
    """

    def __init__(self, model_repository: ModelRepository):
        """
        유스케이스를 초기화합니다.

        Args:
            model_repository: ML 모델 작업을 위한 리포지토리
        """
        self._model_repository = model_repository

    async def execute(self, image_data: bytes, image_format: str = None) -> Embedding:
        """
        코 이미지에서 임베딩을 추출합니다.

        Args:
            image_data: 원본 이미지 바이트
            image_format: 선택적 이미지 형식 (jpeg, png 등)

        Returns:
            추출된 임베딩

        Raises:
            InvalidImageError: 이미지가 유효하지 않은 경우
            ModelNotLoadedError: 모델이 로드되지 않은 경우
            InferenceError: 추론이 실패한 경우
        """
        logger.info(
            f"이미지에서 임베딩 추출 중 "
            f"(크기: {len(image_data)} bytes, 형식: {image_format})"
        )

        # 도메인 엔티티 생성
        try:
            nose_image = NoseImage(
                image_data=image_data,
                image_format=image_format
            )
        except ValueError as e:
            raise InvalidImageError(str(e))

        # 리포지토리를 통해 도메인 로직 실행
        embedding = await self._model_repository.extract_embedding(nose_image)

        logger.info(f"임베딩 추출 성공 (차원: {embedding.dimension})")

        return embedding