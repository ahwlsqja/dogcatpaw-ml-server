"""이미지 전처리."""
import numpy as np
from PIL import Image
import io
import logging

from ...domain.exceptions import InvalidImageError

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """
    ONNX 모델을 위한 이미지 전처리.

    이미지 변환, 크기 조정 및 정규화를 처리합니다.
    """

    def __init__(
        self,
        target_size: int = 96,
        channels: int = 1,
        center_crop_ratio: float = 0.6,
        enable_crop: bool = True,
    ):
        """
        전처리기를 초기화합니다.

        Args:
            target_size: 목표 이미지 크기 (너비와 높이)
            channels: 채널 수 (그레이스케일은 1, RGB는 3)
            center_crop_ratio: 중앙 crop 비율 (0.0 ~ 1.0, 예: 0.6 = 60%)
            enable_crop: 중앙 crop 활성화 여부
        """
        self.target_size = target_size
        self.channels = channels
        self.center_crop_ratio = center_crop_ratio
        self.enable_crop = enable_crop

    def center_crop(self, image: Image.Image) -> Image.Image:
        """
        이미지 중앙 영역을 crop합니다 (코가 중앙에 있다고 가정).

        Args:
            image: PIL Image 객체

        Returns:
            중앙이 crop된 PIL Image 객체
        """
        width, height = image.size

        # crop 크기 계산 (원본 이미지의 center_crop_ratio만큼)
        crop_width = int(width * self.center_crop_ratio)
        crop_height = int(height * self.center_crop_ratio)

        # crop 좌표 계산 (중앙 기준)
        left = (width - crop_width) // 2
        top = (height - crop_height) // 2
        right = left + crop_width
        bottom = top + crop_height

        logger.debug(
            f"중앙 crop: 원본 크기 ({width}x{height}) → "
            f"crop 크기 ({crop_width}x{crop_height}), "
            f"좌표 ({left}, {top}, {right}, {bottom})"
        )

        return image.crop((left, top, right, bottom))

    def preprocess(self, image_bytes: bytes) -> np.ndarray:
        """
        모델 입력을 위해 이미지를 전처리합니다.

        Args:
            image_bytes: 원본 이미지 바이트

        Returns:
            모델 입력을 위해 준비된 전처리된 numpy 배열

        Raises:
            InvalidImageError: 이미지를 처리할 수 없는 경우
        """
        try:
            # 이미지 로드
            image = Image.open(io.BytesIO(image_bytes))
            original_size = image.size
            logger.debug(f"원본 이미지 크기: {original_size}")

            # 중앙 crop (코 영역 추출)
            if self.enable_crop:
                image = self.center_crop(image)
                logger.info(
                    f"중앙 crop 적용: {original_size} → {image.size} "
                    f"(비율: {self.center_crop_ratio:.0%})"
                )

            # 필요한 경우 그레이스케일로 변환
            if self.channels == 1 and image.mode != 'L':
                logger.debug(f"이미지를 {image.mode}에서 그레이스케일로 변환 중")
                image = image.convert('L')
            elif self.channels == 3 and image.mode != 'RGB':
                logger.debug(f"이미지를 {image.mode}에서 RGB로 변환 중")
                image = image.convert('RGB')

            # 크기 조정
            if image.size != (self.target_size, self.target_size):
                logger.debug(
                    f"이미지 크기를 {image.size}에서 "
                    f"({self.target_size}, {self.target_size})로 조정 중"
                )
                image = image.resize((self.target_size, self.target_size))

            # numpy 배열로 변환
            image_array = np.array(image, dtype=np.float32)

            # [0, 1]로 정규화
            image_array = image_array / 255.0

            # 그레이스케일인 경우 채널 차원 추가: (96, 96) -> (96, 96, 1)
            if self.channels == 1 and len(image_array.shape) == 2:
                image_array = np.expand_dims(image_array, axis=-1)

            # 배치 차원 추가: (96, 96, 1) -> (1, 96, 96, 1)
            image_array = np.expand_dims(image_array, axis=0)

            logger.debug(f"전처리된 이미지 형태: {image_array.shape}")

            return image_array

        except Exception as e:
            logger.error(f"이미지 전처리 실패: {e}")
            raise InvalidImageError(f"이미지 전처리 실패: {str(e)}")