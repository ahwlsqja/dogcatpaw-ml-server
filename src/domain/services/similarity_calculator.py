"""벡터 유사도 계산 서비스."""
import math
from typing import List, Tuple


class SimilarityCalculator:
    """
    두 벡터 간의 유사도를 계산하는 도메인 서비스.

    코사인 유사도, 유클리드 거리 등을 계산합니다.
    """

    @staticmethod
    def cosine_similarity(vector1: List[float], vector2: List[float]) -> float:
        """
        두 벡터의 코사인 유사도를 계산합니다.

        Args:
            vector1: 첫 번째 벡터
            vector2: 두 번째 벡터

        Returns:
            코사인 유사도 (-1.0 ~ 1.0, 일반적으로 0.0 ~ 1.0)

        Raises:
            ValueError: 벡터의 차원이 다르거나 0인 경우
        """
        if len(vector1) != len(vector2):
            raise ValueError(
                f"벡터 차원이 다릅니다: {len(vector1)} vs {len(vector2)}"
            )

        if len(vector1) == 0:
            raise ValueError("벡터가 비어있습니다")

        # 내적 계산
        dot_product = sum(a * b for a, b in zip(vector1, vector2))

        # 크기 계산
        magnitude1 = math.sqrt(sum(a * a for a in vector1))
        magnitude2 = math.sqrt(sum(b * b for b in vector2))

        # 0으로 나누는 것 방지
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        # 코사인 유사도
        return dot_product / (magnitude1 * magnitude2)

    @staticmethod
    def euclidean_distance(vector1: List[float], vector2: List[float]) -> float:
        """
        두 벡터의 유클리드 거리를 계산합니다.

        Args:
            vector1: 첫 번째 벡터
            vector2: 두 번째 벡터

        Returns:
            유클리드 거리 (0.0 ~ infinity, 낮을수록 유사)

        Raises:
            ValueError: 벡터의 차원이 다른 경우
        """
        if len(vector1) != len(vector2):
            raise ValueError(
                f"벡터 차원이 다릅니다: {len(vector1)} vs {len(vector2)}"
            )

        # 유클리드 거리 계산
        squared_diff_sum = sum((a - b) ** 2 for a, b in zip(vector1, vector2))
        return math.sqrt(squared_diff_sum)

    @staticmethod
    def normalized_similarity(
        vector1: List[float],
        vector2: List[float]
    ) -> Tuple[float, float, float]:
        """
        두 벡터의 유사도를 계산하고 정규화된 점수를 반환합니다.

        Args:
            vector1: 첫 번째 벡터
            vector2: 두 번째 벡터

        Returns:
            (similarity, cosine_similarity, euclidean_distance) 튜플
            - similarity: 정규화된 유사도 점수 (0.0 ~ 1.0)
            - cosine_similarity: 코사인 유사도
            - euclidean_distance: 유클리드 거리

        Raises:
            ValueError: 벡터의 차원이 다른 경우
        """
        # 코사인 유사도 계산
        cosine_sim = SimilarityCalculator.cosine_similarity(vector1, vector2)

        # 유클리드 거리 계산
        euclidean_dist = SimilarityCalculator.euclidean_distance(
            vector1,
            vector2
        )

        # 정규화된 유사도 점수 계산
        # 코사인 유사도를 0.0 ~ 1.0 범위로 변환
        # (코사인 유사도는 -1 ~ 1 범위이지만, 일반적으로 0 ~ 1)
        similarity = max(0.0, min(1.0, (cosine_sim + 1) / 2))

        # 임베딩 벡터는 일반적으로 정규화되어 있으므로
        # 코사인 유사도를 그대로 사용하는 것이 더 적절할 수 있음
        if cosine_sim >= 0:
            similarity = cosine_sim

        return similarity, cosine_sim, euclidean_dist
