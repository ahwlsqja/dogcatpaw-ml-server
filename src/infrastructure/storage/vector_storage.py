"""NCP Object Storage에서 특징 벡터를 저장/로드하는 서비스."""
import json
import logging
from typing import Optional, List
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class VectorStorageService:
    """
    NCP Object Storage에서 특징 벡터를 저장하고 로드하는 서비스.

    PetDID를 키로 사용하여 특징 벡터를 JSON 형식으로 저장/로드합니다.
    """

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        endpoint: str,
        region: str,
        bucket_name: str,
        vector_prefix: str = "pet-vectors",
    ):
        """
        VectorStorageService를 초기화합니다.

        Args:
            access_key: NCP Access Key
            secret_key: NCP Secret Key
            endpoint: NCP Object Storage 엔드포인트 URL
            region: NCP 리전
            bucket_name: 버킷 이름
            vector_prefix: 벡터 저장 경로 prefix (예: "pet/petDID")
        """
        self.bucket_name = bucket_name
        self.vector_prefix = vector_prefix

        # S3 호환 클라이언트 생성
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint,
            region_name=region,
        )

        logger.info(
            f"VectorStorageService 초기화: bucket={bucket_name}, "
            f"prefix={vector_prefix}"
        )

    def get_vector_by_pet_did(self, pet_did: str) -> Optional[List[float]]:
        """
        PetDID로 저장된 특징 벡터를 가져옵니다.

        Args:
            pet_did: Pet DID (예: "did:pet:12345")

        Returns:
            특징 벡터 리스트, 없으면 None

        Raises:
            Exception: 다운로드 실패 시
        """
        # PetDID를 Object Storage 키로 변환
        # 예: "did:pet:12345" → "pet/petDID/did:pet:12345.json"
        object_key = f"{self.vector_prefix}/{pet_did}.json"

        logger.info(
            f"벡터 키 : {object_key} "
        )

        try:
            logger.info(
                f"벡터 다운로드 시작: bucket={self.bucket_name}, "
                f"key={object_key}"
            )

            # Object Storage에서 벡터 다운로드
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )

            # JSON 데이터 읽기
            json_content = response['Body'].read().decode('utf-8')
            vector_data = json.loads(json_content)

            # 'featureVector' 키로 벡터 가져오기 (NCP 저장 형식)
            vector = vector_data.get('featureVector', [])

            # 벡터가 비어있으면 명확한 에러
            if not vector or len(vector) == 0:
                logger.error(
                    f"벡터 데이터가 비어있습니다! "
                    f"JSON keys: {list(vector_data.keys())}, "
                    f"featureVector value: {vector}"
                )
                raise Exception(
                    f"저장된 벡터가 비어있습니다. "
                    f"JSON 구조를 확인하세요: keys={list(vector_data.keys())}"
                )

            dimension = vector_data.get('vectorSize', len(vector))

            logger.info(
                f"벡터 다운로드 완료: {object_key} "
                f"(차원: {dimension})"
            )

            return vector

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')

            if error_code == 'NoSuchKey':
                logger.warning(f"벡터를 찾을 수 없음: {object_key}")
                return None

            error_msg = e.response.get('Error', {}).get('Message', str(e))
            logger.error(
                f"벡터 다운로드 실패 (ClientError): "
                f"code={error_code}, message={error_msg}"
            )
            raise Exception(
                f"NCP Object Storage에서 벡터 다운로드 실패: {error_msg}"
            ) from e

        except BotoCoreError as e:
            logger.error(f"벡터 다운로드 실패 (BotoCoreError): {e}")
            raise Exception(f"boto3 클라이언트 오류: {str(e)}") from e

        except json.JSONDecodeError as e:
            logger.error(f"벡터 JSON 파싱 실패: {e}")
            raise Exception(f"벡터 JSON 형식 오류: {str(e)}") from e

        except Exception as e:
            logger.error(f"벡터 다운로드 실패 (예상치 못한 오류): {e}")
            raise

    def save_vector(self, pet_did: str, vector: List[float]) -> bool:
        """
        특징 벡터를 PetDID로 저장합니다.

        Args:
            pet_did: Pet DID
            vector: 저장할 특징 벡터

        Returns:
            저장 성공 여부

        Raises:
            Exception: 업로드 실패 시
        """
        object_key = f"{self.vector_prefix}/{pet_did}.json"

        try:
            logger.info(
                f"벡터 업로드 시작: bucket={self.bucket_name}, "
                f"key={object_key}, dimension={len(vector)}"
            )

            # JSON 데이터 생성 (NCP 저장 형식과 동일하게)
            vector_data = {
                "petDID": pet_did,
                "featureVector": vector,
                "vectorSize": len(vector),
                "createdAt": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "version": "1.0"
            }

            # Object Storage에 업로드
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=json.dumps(vector_data, ensure_ascii=False).encode('utf-8'),
                ContentType='application/json'
            )

            logger.info(f"벡터 업로드 완료: {object_key}")
            return True

        except ClientError as e:
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"벡터 업로드 실패 (ClientError): {error_msg}")
            raise Exception(
                f"NCP Object Storage에 벡터 업로드 실패: {error_msg}"
            ) from e

        except BotoCoreError as e:
            logger.error(f"벡터 업로드 실패 (BotoCoreError): {e}")
            raise Exception(f"boto3 클라이언트 오류: {str(e)}") from e

        except Exception as e:
            logger.error(f"벡터 업로드 실패 (예상치 못한 오류): {e}")
            raise

    def check_vector_exists(self, pet_did: str) -> bool:
        """
        PetDID에 해당하는 벡터가 존재하는지 확인합니다.

        Args:
            pet_did: Pet DID

        Returns:
            벡터가 존재하면 True
        """
        object_key = f"{self.vector_prefix}/{pet_did}.json"

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
