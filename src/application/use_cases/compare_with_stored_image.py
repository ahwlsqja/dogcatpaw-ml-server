"""저장된 벡터와 비교하는 유스케이스."""
import logging
from typing import Protocol, Optional, List

from ...domain.entities.nose_image import NoseImage
from ...domain.repositories.model_repository import ModelRepository
from ...domain.services.similarity_calculator import SimilarityCalculator
from ...domain.exceptions import InvalidImageError
from ..dto.embedding_dto import SimilarityDTO

logger = logging.getLogger(__name__)


class VectorStorageProtocol(Protocol):
    """벡터 스토리지 인터페이스."""

    def get_vector_by_pet_did(self, pet_did: str) -> Optional[List[float]]:
        """PetDID로 벡터를 가져옵니다."""
        ...


class ImageStorageProtocol(Protocol):
    """이미지 스토리지 인터페이스."""

    def get_image_by_key(self, image_key: str) -> Optional[bytes]:
        """이미지 키로 이미지를 가져옵니다."""
        ...


class CompareWithStoredImageUseCase:
    """
    NCP에 저장된 이미지와 벡터를 비교하는 유스케이스.

    1. NCP에서 새 이미지 다운로드
    2. 새 이미지에서 특징 벡터 추출
    3. PetDID로 저장된 벡터 로드
    4. 두 벡터의 유사도 계산
    """

    def __init__(
        self,
        model_repository: ModelRepository,
        vector_storage: VectorStorageProtocol,
        image_storage: ImageStorageProtocol,
    ):
        """
        유스케이스를 초기화합니다.

        Args:
            model_repository: ML 모델 작업을 위한 리포지토리
            vector_storage: 벡터 저장소
            image_storage: 이미지 저장소
        """
        self._model_repository = model_repository
        self._vector_storage = vector_storage
        self._image_storage = image_storage
        self._similarity_calculator = SimilarityCalculator()

    async def execute(
        self,
        image_key: str,
        pet_did: str,
    ) -> SimilarityDTO:
        """
        NCP에 저장된 이미지를 저장된 벡터와 비교합니다.

        Args:
            image_key: NCP Object Storage 이미지 키 (예: "nose-print-photo/did:pet:12345/image1.jpg")
            pet_did: 저장된 벡터를 가져오기 위한 Pet DID

        Returns:
            유사도 계산 결과 DTO

        Raises:
            InvalidImageError: 이미지가 유효하지 않은 경우
            ModelNotLoadedError: 모델이 로드되지 않은 경우
            InferenceError: 추론이 실패한 경우
            Exception: 이미지나 벡터를 찾을 수 없거나 로드에 실패한 경우
        """
        logger.info(
            f"이미지 비교 시작: image_key={image_key}, pet_did={pet_did}"
        )

        # 1. NCP에서 새 이미지 다운로드
        image_data = self._image_storage.get_image_by_key(image_key)

        if image_data is None:
            error_msg = f"이미지를 찾을 수 없습니다: {image_key}"
            logger.error(error_msg)
            raise Exception(error_msg)

        logger.info(
            f"이미지 다운로드 완료: {image_key} ({len(image_data)} bytes)"
        )

        # 2. 새 이미지에서 특징 벡터 추출
        try:
            nose_image = NoseImage(
                image_data=image_data,
                image_format=None  # 자동 감지
            )
        except ValueError as e:
            raise InvalidImageError(str(e))

        new_embedding = await self._model_repository.extract_embedding(nose_image)
        new_vector = new_embedding.vector

        logger.info(
            f"새 이미지 벡터 추출 완료 (차원: {new_embedding.dimension})"
        )

        # 3. PetDID로 저장된 벡터 로드
        stored_vector = self._vector_storage.get_vector_by_pet_did(pet_did)

        if stored_vector is None:
            error_msg = f"PetDID '{pet_did}'에 해당하는 벡터를 찾을 수 없습니다"
            logger.error(error_msg)
            raise Exception(error_msg)

        logger.info(
            f"저장된 벡터 로드 완료: pet_did={pet_did}, "
            f"차원={len(stored_vector)}"
        )

        # 벡터 차원 검증
        if len(new_vector) != len(stored_vector):
            error_msg = (
                f"벡터 차원이 일치하지 않습니다: "
                f"새 이미지={len(new_vector)}, "
                f"저장된 벡터={len(stored_vector)}"
            )
            logger.error(error_msg)
            raise Exception(error_msg)

        # 4. 유사도 계산
        similarity, cosine_sim, euclidean_dist = (
            self._similarity_calculator.normalized_similarity(
                new_vector,
                stored_vector
            )
        )

        logger.info(
            f"유사도 계산 완료: similarity={similarity:.4f}, "
            f"cosine={cosine_sim:.4f}, euclidean={euclidean_dist:.4f}"
        )

        return SimilarityDTO(
            similarity=similarity,
            cosine_similarity=cosine_sim,
            euclidean_distance=euclidean_dist,
            vector_size=len(new_vector),
            success=True,
            error_message=None
        )
