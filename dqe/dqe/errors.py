from abc import ABC, abstractmethod

from fastapi import HTTPException


class DQEError(Exception, ABC):
    @abstractmethod
    def to_http(self) -> HTTPException:
        pass
