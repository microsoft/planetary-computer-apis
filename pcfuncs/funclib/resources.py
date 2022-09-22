from pathlib import Path


HERE = Path(__file__).parent


class Resources:
    @classmethod
    def logo_path(self) -> Path:
        return HERE.joinpath("resources/ms-logo-sized.jpg")

    @classmethod
    def font_path(self) -> Path:
        return HERE.joinpath("resources/DejaVuSans.ttf")
