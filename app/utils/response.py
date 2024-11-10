from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi import status

T = TypeVar('T')

class ResponseModel(BaseModel, Generic[T]):
    code: int = 200
    message: str = "Success"
    data: Optional[T] = None

def response_success(*, data: any = None, message: str = "Success") -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "code": 200,
            "message": message,
            "data": data
        }
    )

def response_error(*, code: int = 400, message: str = "Bad Request") -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "code": code,
            "message": message,
            "data": None
        }
    )