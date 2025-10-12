"""NCP Object Storage에서 모델을 다운로드하는 모듈."""
import os
import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class ModelDownloader:
    """
    NCP Object Storage에서 ML 모델을 다운로드합니다.

    boto3 S3 클라이언트를 사용하여 NCP Object Storage와 통신합니다.
    (NCP Object Storage는 S3 호환 API를 제공)
    """

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        endpoint: str,
        region: str,
        bucket_name: str,
    ):
        """
        ModelDownloader를 초기화합니다.

        Args:
            access_key: NCP Access Key
            secret_key: NCP Secret Key
            endpoint: NCP Object Storage 엔드포인트 URL
            region: NCP 리전
            bucket_name: 버킷 이름
        """
        self.bucket_name = bucket_name

        # S3 호환 클라이언트 생성
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint,
            region_name=region,
        )

        logger.info(f"ModelDownloader 초기화: bucket={bucket_name}, endpoint={endpoint}")

    async def download_model(
        self,
        object_key: str,
        local_path: str,
        force_download: bool = False
    ) -> str:
        """
        NCP Object Storage에서 모델 파일을 다운로드합니다.

        Args:
            object_key: Object Storage의 객체 키 (예: "models/embedder_model.onnx")
            local_path: 로컬 저장 경로
            force_download: True면 기존 파일이 있어도 다시 다운로드

        Returns:
            다운로드된 파일의 로컬 경로

        Raises:
            Exception: 다운로드 실패 시
        """
        # 이미 파일이 존재하고 force_download가 False면 다운로드 스킵
        if os.path.exists(local_path) and not force_download:
            logger.info(f"모델이 이미 존재함, 다운로드 스킵: {local_path}")
            return local_path

        # 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        try:
            logger.info(
                f"모델 다운로드 시작: bucket={self.bucket_name}, "
                f"key={object_key} -> {local_path}"
            )

            # Object Storage에서 파일 다운로드
            self.s3_client.download_file(
                Bucket=self.bucket_name,
                Key=object_key,
                Filename=local_path
            )

            # 파일 크기 확인
            file_size = os.path.getsize(local_path)
            logger.info(
                f"모델 다운로드 완료: {local_path} "
                f"({file_size / (1024*1024):.2f} MB)"
            )

            return local_path

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))

            logger.error(
                f"모델 다운로드 실패 (ClientError): "
                f"code={error_code}, message={error_msg}"
            )
            raise Exception(
                f"NCP Object Storage에서 모델 다운로드 실패: {error_msg}"
            ) from e

        except BotoCoreError as e:
            logger.error(f"모델 다운로드 실패 (BotoCoreError): {e}")
            raise Exception(f"boto3 클라이언트 오류: {str(e)}") from e

        except Exception as e:
            logger.error(f"모델 다운로드 실패 (예상치 못한 오류): {e}")
            raise

    def check_model_exists(self, object_key: str) -> bool:
        """
        Object Storage에 모델 파일이 존재하는지 확인합니다.

        Args:
            object_key: 확인할 객체 키

        Returns:
            파일이 존재하면 True
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == '404':
                return False
            raise
