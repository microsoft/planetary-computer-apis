from abc import ABC, abstractmethod

from fastapi import HTTPException


class TilerError(Exception, ABC):
    @abstractmethod
    def to_http(self) -> HTTPException:
        pass
