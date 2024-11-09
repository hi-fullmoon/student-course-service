from typing import Any, Optional
from fastapi.responses import JSONResponse

class ResponseModel:
    def __init__(
        self,
        code: int = 200,
        message: str = "success",
        data: Any = None
    ):
        self.code = code
        self.message = message
        self.data = data

    def dict(self):
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data
        }

def response(
    *,
    code: int = 200,
    data: Any = None,
    message: str = "success"
) -> JSONResponse:
    return JSONResponse(
        status_code=200,  # HTTP状态码总是200
        content=ResponseModel(
            code=code,
            message=message,
            data=data
        ).dict()
    )