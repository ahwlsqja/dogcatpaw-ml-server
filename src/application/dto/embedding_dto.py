"""애플리케이션 레이어를 위한 DTO."""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class EmbeddingDTO:
    """
    임베딩 응답을 위한 DTO.

    레이어 간 임베딩 데이터를 전달하는 데 사용됩니다.
    """

    vector: List[float]
    dimension: int
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class HealthStatusDTO:
    """
    헬스 상태 응답을 위한 DTO.

    헬스 체크 결과를 전달하는 데 사용됩니다.
    """

    status: str  # SERVING, NOT_SERVING
    model_loaded: bool
    model_info: Dict[str, Any]
    timestamp: str
    message: Optional[str] = None


@dataclass
class SimilarityDTO:
    """
    벡터 유사도 비교 결과를 위한 DTO.

    두 벡터 간의 유사도 계산 결과를 전달하는 데 사용됩니다.
    """

    similarity: float  # 0.0 ~ 1.0
    cosine_similarity: float
    euclidean_distance: float
    vector_size: int
    success: bool = True
    error_message: Optional[str] = None