from typing import TYPE_CHECKING

from funclib.resources import Resources
from funclib.stamps.stamp import TRANSPARENT, FrameStamp
from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Image as PILImage

if TYPE_CHECKING:
    from animation.frame import AnimationFrame


class LogoStamp(FrameStamp):
    def apply(self, image: PILImage) -> PILImage:
        logo = Image.open(Resources.logo_path())

        RIGHT_OFFSET = 141
        BOTTOM_OFFSET = 55

        x, y = (
            image.width - RIGHT_OFFSET,
            image.height - BOTTOM_OFFSET,
        )

        image.paste(logo, (x, y))

        return image


class PcUrlStamp(FrameStamp):
    def __init__(self, frame: "AnimationFrame"):
        super().__init__(frame)
        self.font = ImageFont.truetype(Resources.font_path(), 12)
        self.text = "planetarycomputer.microsoft.com"
        self.text_width, self.text_height = self.font.getsize(self.text)

    def apply(self, image: PILImage) -> PILImage:
        brand_frame = Image.new("RGBA", (image.width, image.height), TRANSPARENT)

        BOTTOM_OFFSET = 16
        PADDING = 2

        draw = ImageDraw.Draw(brand_frame)
        x, y = (
            image.width - self.text_width - PADDING * 4.5,
            image.height - self.text_height - BOTTOM_OFFSET,
        )

        # Draw an padded background for the text
        draw.rounded_rectangle(
            (
                (x - PADDING, y - self.text_height / 2 + PADDING),
                (x + self.text_width + PADDING, y + self.text_height + PADDING * 2),
            ),
            radius=1,
            fill=(255, 255, 255, 255),
        )

        draw.text(
            (x, y),
            text=self.text,
            font=self.font,
            fill=(0, 0, 0, 255),
        )

        return Image.alpha_composite(image, brand_frame)
