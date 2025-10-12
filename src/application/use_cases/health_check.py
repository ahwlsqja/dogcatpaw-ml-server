"""헬스 체크 유스케이스."""
import logging
from typing import Dict, Any
from datetime import datetime

from ...domain.repositories.model_repository import ModelRepository

logger = logging.getLogger(__name__)


class HealthCheckUseCase:
    """
    서비스 헬스 체크를 위한 유스케이스.

    모델이 로드되어 요청을 처리할 준비가 되었는지 확인합니다.
    """

    def __init__(self, model_repository: ModelRepository):
        """
        유스케이스를 초기화합니다.

        Args:
            model_repository: ML 모델 작업을 위한 리포지토리
        """
        self._model_repository = model_repository

    async def execute(self) -> Dict[str, Any]:
        """
        헬스 체크를 수행합니다.

        Returns:
            헬스 상태 정보가 담긴 딕셔너리
        """
        logger.debug("헬스 체크 수행 중")

        is_healthy = await self._model_repository.is_healthy()
        model_info = await self._model_repository.get_model_info()

        status = {
            "status": "SERVING" if is_healthy else "NOT_SERVING",
            "model_loaded": is_healthy,
            "model_info": model_info,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"헬스 체크 결과: {status['status']}")

        return status