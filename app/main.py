from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from .models import models
from .routers import (
    students, courses, enrollments, auth, reports,
    teachers, classrooms, schedules, reviews, notifications, admin
)
from .utils.init_db import init_database
from .utils.logger import system_logger
from .utils.response import response

init_database()
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="选修课管理系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    system_logger.error(f"Global error: {str(exc)}", exc_info=True)
    return response(code=500, message="服务器内部错误")

app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(students.router, prefix="/api/students", tags=["students"])
app.include_router(teachers.router, prefix="/api/teachers", tags=["teachers"])
app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
app.include_router(classrooms.router, prefix="/api/classrooms", tags=["classrooms"])
app.include_router(schedules.router, prefix="/api/schedules", tags=["schedules"])
app.include_router(enrollments.router, prefix="/api/enrollments", tags=["enrollments"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/")
async def root():
    return {
        "message": "欢迎使用选修课管理系统",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)