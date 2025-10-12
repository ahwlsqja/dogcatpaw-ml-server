"""의존성 주입 컨테이너."""
from dependency_injector import containers, providers

from .infrastructure.config.settings import Settings
from .infrastructure.ml.onnx_model import ONNXModelRepository
from .infrastructure.ml.image_preprocessor import ImagePreprocessor
from .infrastructure.ml.model_downloader import ModelDownloader
from .infrastructure.storage.vector_storage import VectorStorageService
from .infrastructure.storage.image_storage import ImageStorageService
from .infrastructure.grpc.server import GRPCServer
from .application.use_cases.extract_embedding import ExtractEmbeddingUseCase
from .application.use_cases.health_check import HealthCheckUseCase
from .application.use_cases.compare_with_stored_image import (
    CompareWithStoredImageUseCase,
)
from .presentation.grpc.servicer import NoseEmbedderServicer


def create_model_downloader(settings: Settings):
    """NCP Object Storage 설정이 있을 때만 ModelDownloader를 생성합니다."""
    if all([
        settings.ncp_access_key,
        settings.ncp_secret_key,
        settings.ncp_bucket_name,
    ]):
        return ModelDownloader(
            access_key=settings.ncp_access_key,
            secret_key=settings.ncp_secret_key,
            endpoint=settings.ncp_endpoint,
            region=settings.ncp_region,
            bucket_name=settings.ncp_bucket_name,
        )
    return None


def create_vector_storage(settings: Settings):
    """NCP Object Storage 설정이 있을 때만 VectorStorageService를 생성합니다."""
    if all([
        settings.ncp_access_key,
        settings.ncp_secret_key,
        settings.ncp_bucket_name,
    ]):
        return VectorStorageService(
            access_key=settings.ncp_access_key,
            secret_key=settings.ncp_secret_key,
            endpoint=settings.ncp_endpoint,
            region=settings.ncp_region,
            bucket_name=settings.ncp_bucket_name,
            vector_prefix=settings.ncp_vector_prefix,
        )
    return None


def create_image_storage(settings: Settings):
    """NCP Object Storage 설정이 있을 때만 ImageStorageService를 생성합니다."""
    if all([
        settings.ncp_access_key,
        settings.ncp_secret_key,
        settings.ncp_bucket_name,
    ]):
        return ImageStorageService(
            access_key=settings.ncp_access_key,
            secret_key=settings.ncp_secret_key,
            endpoint=settings.ncp_endpoint,
            region=settings.ncp_region,
            bucket_name=settings.ncp_bucket_name,
            image_prefix=settings.ncp_image_prefix,
        )
    return None


class Container(containers.DeclarativeContainer):
    """애플리케이션 DI 컨테이너."""

    # 설정
    config = providers.Singleton(Settings)

    # 인프라스트럭처 - 이미지 전처리
    image_preprocessor = providers.Singleton(
        ImagePreprocessor,
        target_size=config.provided.model_input_size,
        channels=config.provided.model_input_channels,
        center_crop_ratio=config.provided.center_crop_ratio,
        enable_crop=config.provided.enable_center_crop,
    )

    # 인프라스트럭처 - 모델 다운로더 (조건부)
    model_downloader = providers.Singleton(
        create_model_downloader,
        settings=config,
    )

    # 인프라스트럭처 - 벡터 스토리지 (조건부)
    vector_storage = providers.Singleton(
        create_vector_storage,
        settings=config,
    )

    # 인프라스트럭처 - 이미지 스토리지 (조건부)
    image_storage = providers.Singleton(
        create_image_storage,
        settings=config,
    )

    # 인프라스트럭처 - 모델 리포지토리
    model_repository = providers.Singleton(
        ONNXModelRepository,
        model_path=config.provided.model_path,
        input_size=config.provided.model_input_size,
        input_channels=config.provided.model_input_channels,
        model_downloader=model_downloader,
        ncp_model_key=config.provided.ncp_model_key,
        model_cache_dir=config.provided.model_cache_dir,
    )

    # 애플리케이션 - 유스케이스
    extract_embedding_use_case = providers.Factory(
        ExtractEmbeddingUseCase,
        model_repository=model_repository,
    )

    health_check_use_case = providers.Factory(
        HealthCheckUseCase,
        model_repository=model_repository,
    )

    compare_with_stored_image_use_case = providers.Factory(
        CompareWithStoredImageUseCase,
        model_repository=model_repository,
        vector_storage=vector_storage,
        image_storage=image_storage,
    )

    # 프레젠테이션 - gRPC Servicer
    nose_embedder_servicer = providers.Singleton(
        NoseEmbedderServicer,
        extract_embedding_use_case=extract_embedding_use_case,
        health_check_use_case=health_check_use_case,
        compare_with_stored_image_use_case=compare_with_stored_image_use_case,
    )

    # 인프라스트럭처 - gRPC 서버
    grpc_server = providers.Singleton(
        GRPCServer,
        port=config.provided.grpc_port,
        max_workers=config.provided.grpc_workers,
        max_message_length=config.provided.grpc_max_message_length,
    )