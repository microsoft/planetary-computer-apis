from typing import TYPE_CHECKING

from abc import ABC, abstractmethod
from PIL.Image import Image as PILImage


if TYPE_CHECKING:
    from animation.frame import AnimationFrame

TRANSPARENT = (255, 255, 255, 0)

class FrameStamp(ABC):
    def __init__(self, frame: "AnimationFrame") -> None:
        self.frame = frame

    @abstractmethod
    def apply(self, image: PILImage) -> PILImage:
        pass
