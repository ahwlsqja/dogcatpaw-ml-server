"""비동기 gRPC 서버 구현."""
import grpc
import logging
from concurrent import futures
from typing import Callable

logger = logging.getLogger(__name__)


class GRPCServer:
    """
    비동기 gRPC 서버.

    효율적인 비동기 I/O 작업을 위해 grpc.aio.server를 기반으로 합니다.
    참고: https://grpc.io/docs/languages/python/async/
    """

    def __init__(
        self,
        port: int = 50052,
        max_workers: int = 10,
        max_message_length: int = 10 * 1024 * 1024,
    ):
        """
        gRPC 서버를 초기화합니다.

        Args:
            port: 서버 포트
            max_workers: ThreadPool 최대 워커 수
            max_message_length: 최대 메시지 크기 (바이트)
        """
        self.port = port
        self.max_workers = max_workers
        self.max_message_length = max_message_length

        # 비동기 서버 생성
        self._server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=max_workers),
            options=[
                ('grpc.max_receive_message_length', max_message_length),
                ('grpc.max_send_message_length', max_message_length),
            ]
        )

    def add_servicer(self, servicer_adder: Callable, servicer: any) -> None:
        """
        서버에 서비서를 추가합니다.

        Args:
            servicer_adder: 서비서를 추가하는 함수 (protoc에 의해 생성됨)
            servicer: 서비서 인스턴스
        """
        servicer_adder(servicer, self._server)
        logger.info(f"서비서 추가됨: {servicer.__class__.__name__}")

    async def start(self) -> None:
        """gRPC 서버를 시작합니다."""
        self._server.add_insecure_port(f'[::]:{self.port}')
        await self._server.start()

        logger.info(
            f"비동기 gRPC 서버 시작됨\n"
            f"  포트: {self.port}\n"
            f"  워커 수: {self.max_workers}\n"
            f"  최대 메시지 길이: {self.max_message_length / 1024 / 1024:.1f}MB"
        )

    async def serve(self) -> None:
        """
        무한히 서비스합니다.

        서버가 중지될 때까지 블로킹됩니다.
        """
        await self._server.wait_for_termination()

    async def stop(self, grace: float = 5.0) -> None:
        """
        gRPC 서버를 안전하게 중지합니다.

        Args:
            grace: 유예 시간 (초)
        """
        logger.info(f"gRPC 서버 중지 중 (유예 시간: {grace}초)")
        await self._server.stop(grace)
        logger.info("gRPC 서버 중지됨")