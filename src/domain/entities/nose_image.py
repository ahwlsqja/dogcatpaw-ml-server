"""코 이미지 엔티티."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class NoseImage:
    """
    반려견 코 이미지 엔티티.

    임베딩 추출을 위해 처리될 이미지를 나타냅니다.
    값 객체 - 불변이며 값으로 비교됩니다.
    """

    image_data: bytes
    image_format: Optional[str] = None

    def __post_init__(self):
        """이미지 데이터를 검증합니다."""
        if not self.image_data:
            raise ValueError("이미지 데이터는 비어있을 수 없습니다")

        if len(self.image_data) == 0:
            raise ValueError("이미지 데이터의 길이가 0입니다")

    @property
    def size_bytes(self) -> int:
        """이미지 크기를 바이트 단위로 가져옵니다."""
        return len(self.image_data)