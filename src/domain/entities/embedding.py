"""임베딩 엔티티."""
from dataclasses import dataclass
from typing import List
import numpy as np


@dataclass(frozen=True)
class Embedding:
    """
    코 임베딩 벡터 엔티티.

    반려견 코 이미지에서 추출된 특징 벡터를 나타냅니다.
    ML 출력을 나타내는 핵심 도메인 모델입니다.
    """

    vector: List[float]

    def __post_init__(self):
        """임베딩 벡터를 검증합니다."""
        if not self.vector:
            raise ValueError("임베딩 벡터는 비어있을 수 없습니다")

        if not all(isinstance(v, (int, float)) for v in self.vector):
            raise ValueError("모든 벡터 요소는 숫자여야 합니다")

    @property
    def dimension(self) -> int:
        """벡터 차원을 가져옵니다."""
        return len(self.vector)

    @property
    def as_numpy(self) -> np.ndarray:
        """numpy 배열로 변환합니다."""
        return np.array(self.vector, dtype=np.float32)

    def similarity(self, other: "Embedding") -> float:
        """
        다른 임베딩과의 코사인 유사도를 계산합니다.

        Args:
            other: 비교할 다른 임베딩

        Returns:
            -1과 1 사이의 코사인 유사도 점수
        """
        if self.dimension != other.dimension:
            raise ValueError(
                f"차원 불일치: {self.dimension} vs {other.dimension}"
            )

        a = self.as_numpy
        b = other.as_numpy

        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))