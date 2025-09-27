from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class Result(BaseModel, Generic[T]):
    code: int
    message: str
    data: Optional[T] = None

    @staticmethod
    def success(data: Optional[T] = None, message: str = "success") -> "Result[T]":
        return Result(code=200, message=message, data=data)

    @staticmethod
    def error(message: str = "error", code: int = 500) -> "Result[None]":
        return Result(code=code, message=message, data=None)
