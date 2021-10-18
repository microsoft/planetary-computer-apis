import os


class TestData:
    @staticmethod
    def get_path(rel_path):
        return os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "data-files", rel_path)
        )
