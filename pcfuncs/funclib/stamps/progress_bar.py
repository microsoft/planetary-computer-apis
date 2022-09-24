from PIL import Image, ImageDraw
from PIL.Image import Image as PILImage

from .stamp import TRANSPARENT, ImageStamp

BAR_HEIGHT = 3
BG_PAD = 0.2


class ProgressBarStamp(ImageStamp):
    def __init__(self, frame_number: int, frame_count: int) -> None:
        self.frame_number = frame_number
        self.frame_count = frame_count

    def apply(self, image: PILImage) -> PILImage:
        bar_frame = Image.new("RGBA", (image.width, image.height), TRANSPARENT)

        bar_width = int(image.width * (self.frame_number / (self.frame_count - 1)))

        draw = ImageDraw.Draw(bar_frame)
        x0, y0 = 0, image.height - BAR_HEIGHT
        x1, y1 = bar_width, image.height

        # Draw an offset white "background" for the progress bar to stand out against
        draw.rectangle(
            ((x0, y0 - BG_PAD), (x1, y1 - BG_PAD)), fill=(255, 255, 255, 255)
        )
        draw.rectangle(((x0, y0), (x1, y1)), fill=(0, 120, 212, 255))

        return Image.alpha_composite(image, bar_frame)
