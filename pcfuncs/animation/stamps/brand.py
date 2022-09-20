from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Image as PILImage

from .stamp import TRANSPARENT, FrameStamp

BOTTOM_OFFSET = 16
PADDING = 2


text = "planetarycomputer.microsoft.com"
font = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans.ttf", 12)
text_width, text_height = font.getsize(text)


class BrandStamp(FrameStamp):
    def apply(self, image: PILImage) -> PILImage:
        bar_frame = Image.new("RGBA", (image.width, image.height), TRANSPARENT)

        draw = ImageDraw.Draw(bar_frame)
        x, y = (
            image.width - text_width - PADDING * 4.5,
            image.height - text_height - BOTTOM_OFFSET,
        )

        # Draw an padded background for the text
        draw.rounded_rectangle(
            (
                (x - PADDING, y - text_height / 2 + PADDING),
                (x + text_width + PADDING, y + text_height + PADDING * 2),
            ),
            radius=2,
            fill=(255, 255, 255, 255),
        )

        draw.text(
            (x, y),
            text=text,
            font=font,
            fill=(0, 0, 0, 255),
        )

        return Image.alpha_composite(image, bar_frame)
