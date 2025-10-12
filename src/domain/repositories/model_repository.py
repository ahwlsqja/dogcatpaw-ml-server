"""모델 리포지토리 인터페이스."""
from abc import ABC, abstractmethod
from typing import Protocol

from ..entities.embedding import Embedding
from ..entities.nose_image import NoseImage


class ModelRepository(ABC):
    """
    ML 모델 작업을 위한 리포지토리 인터페이스.

    헥사고날 아키텍처의 포트 - 구현 방법을 명시하지 않고
    ML 모델에 필요한 것을 정의합니다.
    """

    @abstractmethod
    async def extract_embedding(self, image: NoseImage) -> Embedding:
        """
        코 이미지에서 임베딩 벡터를 추출합니다.

        Args:
            image: 처리할 코 이미지

        Returns:
            추출된 임베딩 벡터

        Raises:
            ModelNotLoadedError: 모델이 로드되지 않은 경우
            InferenceError: 추론이 실패한 경우
        """
        pass

    @abstractmethod
    async def is_healthy(self) -> bool:
        """
        모델이 로드되어 준비되었는지 확인합니다.

        Returns:
            모델이 정상이면 True, 그렇지 않으면 False
        """
        pass

    @abstractmethod
    async def get_model_info(self) -> dict:
        """
        모델 메타데이터를 가져옵니다.

        Returns:
            모델 정보가 담긴 딕셔너리 (입력 형태, 출력 형태 등)
        """
        pass