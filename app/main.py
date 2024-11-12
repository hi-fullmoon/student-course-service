from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routers import auth, classrooms, courses, schedules, students
from app.utils.auth import oauth2_scheme
from app.utils.init_db import init_database
from app.utils.response import response_error


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


app = FastAPI(title="学生选课系统", lifespan=lifespan)


# 全局异常处理
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return response_error(code=exc.status_code, message=str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return response_error(code=422, message=str(exc.errors()))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return response_error(code=500, message=str(exc))


# 注册路由
app.include_router(auth.router, prefix="/api", tags=["认证"])
app.include_router(
    courses.router,
    prefix="/api",
    tags=["课程管理"],
    dependencies=[Depends(oauth2_scheme)],
)
app.include_router(
    students.router,
    prefix="/api",
    tags=["学生管理"],
    dependencies=[Depends(oauth2_scheme)],
)
app.include_router(
    schedules.router,
    prefix="/api",
    tags=["课程表"],
    dependencies=[Depends(oauth2_scheme)],
)
app.include_router(
    classrooms.router,
    prefix="/api",
    tags=["教室管理"],
    dependencies=[Depends(oauth2_scheme)],
)


@app.get("/")
async def root():
    return {"message": "欢迎使用学生选课系统"}
