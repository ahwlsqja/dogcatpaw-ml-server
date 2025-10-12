"""NCP Object Storage에서 이미지를 가져오는 서비스."""
import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class ImageStorageService:
    """
    NCP Object Storage에서 이미지를 다운로드하는 서비스.

    PetDID를 키로 사용하여 저장된 이미지를 가져옵니다.
    """

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        endpoint: str,
        region: str,
        bucket_name: str,
        image_prefix: str = "pet-images",
    ):
        """
        ImageStorageService를 초기화합니다.

        Args:
            access_key: NCP Access Key
            secret_key: NCP Secret Key
            endpoint: NCP Object Storage 엔드포인트 URL
            region: NCP 리전
            bucket_name: 버킷 이름
            image_prefix: 이미지 저장 경로 prefix (예: "pet-images")
        """
        self.bucket_name = bucket_name
        self.image_prefix = image_prefix

        # S3 호환 클라이언트 생성
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint,
            region_name=region,
        )

        logger.info(
            f"ImageStorageService 초기화: bucket={bucket_name}, "
            f"prefix={image_prefix}"
        )

    def get_image_by_key(self, image_key: str) -> Optional[bytes]:
        """
        이미지 키로 이미지를 가져옵니다.

        Args:
            image_key: Object Storage 키 (예: "nose-print-photo/did:pet:12345/image1.jpg")

        Returns:
            이미지 바이트 데이터, 없으면 None

        Raises:
            Exception: 다운로드 실패 시
        """
        try:
            logger.info(
                f"이미지 다운로드 시작: bucket={self.bucket_name}, "
                f"key={image_key}"
            )

            # Object Storage에서 이미지 다운로드
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=image_key
            )

            # 이미지 데이터 읽기
            image_data = response['Body'].read()
            image_size = len(image_data)

            logger.info(
                f"이미지 다운로드 완료: {image_key} "
                f"({image_size / 1024:.2f} KB)"
            )

            return image_data

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')

            if error_code == 'NoSuchKey':
                logger.warning(f"이미지를 찾을 수 없음: {image_key}")
                return None

            error_msg = e.response.get('Error', {}).get('Message', str(e))
            logger.error(
                f"이미지 다운로드 실패 (ClientError): "
                f"code={error_code}, message={error_msg}"
            )
            raise Exception(
                f"NCP Object Storage에서 이미지 다운로드 실패: {error_msg}"
            ) from e

        except BotoCoreError as e:
            logger.error(f"이미지 다운로드 실패 (BotoCoreError): {e}")
            raise Exception(f"boto3 클라이언트 오류: {str(e)}") from e

        except Exception as e:
            logger.error(f"이미지 다운로드 실패 (예상치 못한 오류): {e}")
            raise

    def get_image_by_pet_did(self, pet_did: str) -> Optional[bytes]:
        """
        PetDID로 이미지를 가져옵니다.

        Args:
            pet_did: Pet DID (예: "did:pet:12345")

        Returns:
            이미지 바이트 데이터, 없으면 None

        Raises:
            Exception: 다운로드 실패 시
        """
        # PetDID를 Object Storage 키로 변환
        # 예: "did:pet:12345" → "pet-images/did:pet:12345.jpg"
        object_key = f"{self.image_prefix}/{pet_did}.jpg"

        try:
            logger.info(
                f"이미지 다운로드 시작: bucket={self.bucket_name}, "
                f"key={object_key}"
            )

            # Object Storage에서 이미지 다운로드
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )

            # 이미지 데이터 읽기
            image_data = response['Body'].read()
            image_size = len(image_data)

            logger.info(
                f"이미지 다운로드 완료: {object_key} "
                f"({image_size / 1024:.2f} KB)"
            )

            return image_data

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')

            if error_code == 'NoSuchKey':
                logger.warning(f"이미지를 찾을 수 없음: {object_key}")
                return None

            error_msg = e.response.get('Error', {}).get('Message', str(e))
            logger.error(
                f"이미지 다운로드 실패 (ClientError): "
                f"code={error_code}, message={error_msg}"
            )
            raise Exception(
                f"NCP Object Storage에서 이미지 다운로드 실패: {error_msg}"
            ) from e

        except BotoCoreError as e:
            logger.error(f"이미지 다운로드 실패 (BotoCoreError): {e}")
            raise Exception(f"boto3 클라이언트 오류: {str(e)}") from e

        except Exception as e:
            logger.error(f"이미지 다운로드 실패 (예상치 못한 오류): {e}")
            raise

    def check_image_exists(self, pet_did: str) -> bool:
        """
        PetDID에 해당하는 이미지가 존재하는지 확인합니다.

        Args:
            pet_did: Pet DID

        Returns:
            이미지가 존재하면 True
        """
        object_key = f"{self.image_prefix}/{pet_did}.jpg"

        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == '404':
                return False
            raise
