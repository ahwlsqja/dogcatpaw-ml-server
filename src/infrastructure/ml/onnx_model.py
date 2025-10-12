"""ONNX 모델 리포지토리 구현."""
import os
import logging
from typing import Dict, Any, Optional
import onnxruntime as ort
import numpy as np

from ...domain.entities.embedding import Embedding
from ...domain.entities.nose_image import NoseImage
from ...domain.repositories.model_repository import ModelRepository
from ...domain.exceptions import ModelNotLoadedError, InferenceError
from .image_preprocessor import ImagePreprocessor
from .model_downloader import ModelDownloader

logger = logging.getLogger(__name__)


class ONNXModelRepository(ModelRepository):
    """
    ModelRepository의 ONNX Runtime 구현.

    헥사고날 아키텍처의 어댑터 - ONNX Runtime을 사용하여
    ModelRepository에 의해 정의된 포트를 구현합니다.
    """

    def __init__(
        self,
        model_path: str,
        input_size: int = 96,
        input_channels: int = 1,
        model_downloader: Optional[ModelDownloader] = None,
        ncp_model_key: Optional[str] = None,
        model_cache_dir: str = "/tmp/models"
    ):
        """
        ONNX 모델을 초기화합니다.

        Args:
            model_path: ONNX 모델 파일 경로 (로컬 또는 기본 경로)
            input_size: 예상 입력 이미지 크기
            input_channels: 예상 입력 채널 수 (그레이스케일은 1)
            model_downloader: NCP Object Storage 다운로더 (선택사항)
            ncp_model_key: NCP Object Storage 객체 키 (선택사항)
            model_cache_dir: 다운로드한 모델 캐시 디렉토리
        """
        self.model_path = model_path
        self.input_size = input_size
        self.input_channels = input_channels
        self.model_downloader = model_downloader
        self.ncp_model_key = ncp_model_key
        self.model_cache_dir = model_cache_dir

        self._session: Optional[ort.InferenceSession] = None
        self._preprocessor = ImagePreprocessor(
            target_size=input_size,
            channels=input_channels
        )

        self._input_name: Optional[str] = None
        self._output_name: Optional[str] = None
        self._model_loaded = False
        self._actual_model_path: Optional[str] = None  # 실제 로드된 모델 경로

    async def load_model(self) -> None:
        """
        ONNX 모델을 로드합니다.

        NCP Object Storage가 설정된 경우 먼저 다운로드하고,
        그렇지 않으면 로컬 경로에서 로드합니다.

        Raises:
            ModelNotLoadedError: 모델 파일이 존재하지 않거나 로딩이 실패한 경우
        """
        # NCP Object Storage에서 다운로드할지 결정
        if self.model_downloader and self.ncp_model_key:
            logger.info(
                f"NCP Object Storage에서 모델 다운로드 시작: {self.ncp_model_key}"
            )

            # 캐시 경로 생성
            cache_filename = os.path.basename(self.ncp_model_key)
            cache_path = os.path.join(self.model_cache_dir, cache_filename)

            try:
                # NCP Object Storage에서 모델 다운로드
                self._actual_model_path = await self.model_downloader.download_model(
                    object_key=self.ncp_model_key,
                    local_path=cache_path,
                    force_download=False  # 캐시된 파일이 있으면 재사용
                )
                logger.info(f"모델 다운로드 완료: {self._actual_model_path}")
            except Exception as e:
                logger.error(f"NCP Object Storage에서 다운로드 실패: {e}")
                raise ModelNotLoadedError(
                    f"NCP Object Storage에서 모델 다운로드 실패: {str(e)}"
                )
        else:
            # 로컬 파일 경로 사용
            logger.info(f"로컬 경로에서 ONNX 모델 로딩: {self.model_path}")
            self._actual_model_path = self.model_path

        # 모델 파일 존재 확인
        if not os.path.exists(self._actual_model_path):
            raise ModelNotLoadedError(
                f"모델 파일을 찾을 수 없음: {self._actual_model_path}"
            )

        try:
            # ONNX Runtime 세션 생성
            self._session = ort.InferenceSession(
                self._actual_model_path,
                providers=['CPUExecutionProvider']
            )

            # 입력/출력 이름 가져오기
            self._input_name = self._session.get_inputs()[0].name
            self._output_name = self._session.get_outputs()[0].name

            input_shape = self._session.get_inputs()[0].shape
            output_shape = self._session.get_outputs()[0].shape

            logger.info(
                f"모델 로드 성공\n"
                f"  경로: {self._actual_model_path}\n"
                f"  입력: {self._input_name}, 형태: {input_shape}\n"
                f"  출력: {self._output_name}, 형태: {output_shape}\n"
                f"  제공자: {self._session.get_providers()}"
            )

            self._model_loaded = True

        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            raise ModelNotLoadedError(f"모델 로드 실패: {str(e)}")

    async def extract_embedding(self, image: NoseImage) -> Embedding:
        """
        코 이미지에서 임베딩을 추출합니다.

        Args:
            image: 코 이미지 엔티티

        Returns:
            임베딩 엔티티

        Raises:
            ModelNotLoadedError: 모델이 로드되지 않은 경우
            InferenceError: 추론이 실패한 경우
        """
        if not self._model_loaded or self._session is None:
            raise ModelNotLoadedError("모델이 로드되지 않았습니다. 먼저 load_model()을 호출하세요.")

        try:
            # 이미지 전처리
            input_array = self._preprocessor.preprocess(image.image_data)

            # 추론 실행
            logger.debug(f"이미지에 대해 추론 실행 중 (크기: {image.size_bytes} bytes)")

            outputs = self._session.run(
                [self._output_name],
                {self._input_name: input_array}
            )

            # 벡터 추출
            vector = outputs[0].flatten().tolist()

            logger.debug(f"추론 성공, 벡터 차원: {len(vector)}")

            return Embedding(vector=vector)

        except Exception as e:
            logger.error(f"추론 실패: {e}")
            raise InferenceError(
                f"임베딩 추출 실패: {str(e)}",
                original_error=e
            )

    async def is_healthy(self) -> bool:
        """
        모델이 로드되어 준비되었는지 확인합니다.

        Returns:
            모델이 정상이면 True
        """
        return self._model_loaded and self._session is not None

    async def get_model_info(self) -> Dict[str, Any]:
        """
        모델 메타데이터를 가져옵니다.

        Returns:
            모델 정보가 담긴 딕셔너리
        """
        if not self._session:
            return {
                "loaded": False,
                "model_path": self.model_path,
                "ncp_model_key": self.ncp_model_key,
            }

        input_shape = self._session.get_inputs()[0].shape
        output_shape = self._session.get_outputs()[0].shape

        return {
            "loaded": self._model_loaded,
            "model_path": self.model_path,
            "actual_model_path": self._actual_model_path,
            "ncp_model_key": self.ncp_model_key,
            "input_name": self._input_name,
            "input_shape": str(input_shape),
            "output_name": self._output_name,
            "output_shape": str(output_shape),
            "providers": self._session.get_providers(),
        }