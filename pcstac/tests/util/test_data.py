import os


class TestData:
    @staticmethod
    def get_path(rel_path: str) -> str:
        return os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "data-files", rel_path)
        )
