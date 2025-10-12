"""애플리케이션 설정."""
import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    애플리케이션 설정.

    환경 변수 관리를 위해 pydantic-settings를 사용합니다.
    """

    # 서버 설정
    grpc_port: int = 50052
    grpc_workers: int = 3  # 공모전용 최적화 (기존 10 → 3)
    grpc_max_message_length: int = 10 * 1024 * 1024  # 10MB

    # 모델 설정
    model_path: str = "embedder_model.onnx"
    model_input_size: int = 96
    model_input_channels: int = 1  # 그레이스케일

    # 이미지 전처리 설정
    center_crop_ratio: float = 0.6  # 중앙 crop 비율 (0.6 = 60%)
    enable_center_crop: bool = True  # 중앙 crop 활성화

    # 로깅
    log_level: str = "INFO"
    log_format: str = "json"  # json 또는 text

    # 환경
    environment: str = "production"  # development, staging, production

    # NCP Object Storage 설정
    ncp_access_key: Optional[str] = None
    ncp_secret_key: Optional[str] = None
    ncp_endpoint: str = "https://kr.object.ncloudstorage.com"
    ncp_region: str = "kr-standard"
    ncp_bucket_name: Optional[str] = None
    ncp_model_key: Optional[str] = None  # 예: "models/embedder_model.onnx"
    ncp_vector_prefix: str = "pet/petDID"  # 벡터 저장 경로 prefix
    ncp_image_prefix: str = "pet-images"  # 이미지 저장 경로 prefix

    # 모델 캐시 설정
    model_cache_dir: str = "/tmp/models"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    캐시된 설정 인스턴스를 가져옵니다.

    Returns:
        Settings 인스턴스
    """
    return Settings()