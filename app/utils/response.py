from datetime import datetime
from decimal import Decimal
from typing import Any, Generic, Optional, TypeVar

from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    code: int = 200
    message: str = "Success"
    data: Optional[T] = None


def response_success(*, data: any = None, message: str = "Success") -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"code": 200, "message": message, "data": data},
    )


def response_error(*, code: int = 400, message: str = "Bad Request") -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"code": code, "message": message, "data": None},
    )


def model_to_dict(model: Any) -> dict:
    """
    将 SQLAlchemy 模型对象转换为字典

    Args:
        model: SQLAlchemy 模型实例

    Returns:
        dict: 包含模型属性的字典
    """
    result = {}
    for column in model.__table__.columns:
        value = getattr(model, column.name)
        # 处理不同类型的值
        if isinstance(value, datetime):
            result[column.name] = value.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(value, Decimal):
            result[column.name] = float(value)
        else:
            result[column.name] = value
    return result
