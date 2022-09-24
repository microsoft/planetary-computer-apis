from abc import ABC, abstractmethod

from PIL.Image import Image as PILImage

TRANSPARENT = (255, 255, 255, 0)


class ImageStamp(ABC):
    @abstractmethod
    def apply(self, image: PILImage) -> PILImage:
        pass
