"""gRPC 서버의 메인 진입점."""
import asyncio
import logging
import signal
from typing import Optional

from .containers import Container


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class Application:
    """메인 애플리케이션 오케스트레이터."""

    def __init__(self):
        """애플리케이션을 초기화합니다."""
        self.container = Container()
        self.server: Optional[object] = None
        self._shutdown_event = asyncio.Event()

    async def startup(self) -> None:
        """
        애플리케이션을 초기화하고 시작합니다.

        다음을 포함합니다:
        1. ML 모델 로딩
        2. gRPC 서버 설정
        3. 서버 시작
        """
        try:
            logger.info("Dog Nose Embedder gRPC 서버 시작 중...")

            # ML 모델 로드
            logger.info("ONNX 모델 로딩 중...")
            model_repository = self.container.model_repository()
            await model_repository.load_model()
            logger.info("모델 로드 성공")

            # gRPC 서버 및 servicer 가져오기
            self.server = self.container.grpc_server()
            servicer = self.container.nose_embedder_servicer()

            # 서버에 servicer 추가
            # 참고: 이 import는 순환 의존성을 피하고
            # proto 파일이 생성되었는지 확인하기 위해 여기서 발생합니다
            try:
                import nose_embedder_pb2_grpc

                self.server.add_servicer(
                    nose_embedder_pb2_grpc.add_NoseEmbedderServiceServicer_to_server,
                    servicer
                )
            except ImportError as e:
                logger.error(
                    "생성된 protobuf 파일을 import하는 데 실패했습니다. "
                    "다음을 실행하세요: python -m grpc_tools.protoc "
                    "-I./src/presentation/proto "
                    "--python_out=. "
                    "--grpc_python_out=. "
                    "./src/presentation/proto/nose_embedder.proto"
                )
                raise

            # gRPC 서버 시작
            await self.server.start()

            logger.info("✓ 애플리케이션이 성공적으로 시작되었습니다")

        except Exception as e:
            logger.exception(f"애플리케이션 시작 실패: {e}")
            raise

    async def shutdown(self) -> None:
        """애플리케이션을 안전하게 종료합니다."""
        logger.info("애플리케이션 종료 중...")

        if self.server:
            await self.server.stop(grace=5.0)

        logger.info("애플리케이션 종료 완료")

    async def run(self) -> None:
        """중단될 때까지 애플리케이션을 실행합니다."""
        # 시그널 핸들러 설정
        def signal_handler(sig, frame):
            logger.info(f"시그널 {sig} 수신")
            self._shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # 애플리케이션 시작
            await self.startup()

            # 종료 시그널 대기
            logger.info("서버가 실행 중입니다. 중지하려면 Ctrl+C를 누르세요.")

            # 종료 이벤트가 설정되거나 서버가 종료될 때까지 실행
            await asyncio.gather(
                self._shutdown_event.wait(),
                self.server.serve(),
                return_exceptions=True
            )

        except KeyboardInterrupt:
            logger.info("키보드 인터럽트 수신")
        except Exception as e:
            logger.exception(f"애플리케이션 에러: {e}")
        finally:
            await self.shutdown()


async def main():
    """메인 진입점."""
    app = Application()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())