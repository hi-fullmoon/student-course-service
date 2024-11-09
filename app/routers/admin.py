from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..utils.auth import get_current_active_user
from ..config import get_settings, Settings
from ..utils.logger import system_logger
from datetime import datetime

router = APIRouter()

@router.get("/system/status")
def get_system_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    settings: Settings = Depends(get_settings)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以查看系统状态")

    # 统计数据
    total_students = db.query(models.Student).count()
    total_teachers = db.query(models.Teacher).count()
    total_courses = db.query(models.Course).count()
    total_enrollments = db.query(models.Enrollment).count()

    return {
        "system_status": {
            "course_selection_enabled": settings.COURSE_SELECTION_ENABLED,
            "grade_input_enabled": settings.GRADE_INPUT_ENABLED
        },
        "statistics": {
            "total_students": total_students,
            "total_teachers": total_teachers,
            "total_courses": total_courses,
            "total_enrollments": total_enrollments
        }
    }

@router.put("/system/settings")
def update_system_settings(
    settings_update: Dict,
    current_user: models.User = Depends(get_current_active_user),
    settings: Settings = Depends(get_settings)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以修改系统设置")

    # 更新设置
    for key, value in settings_update.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
            system_logger.info(f"System setting updated: {key} = {value}")

    return {"message": "系统设置已更新"}

@router.post("/system/maintenance")
def system_maintenance(
    operation: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以执行维护操作")

    if operation == "clear_expired_enrollments":
        # 清理过期的选课记录
        result = db.query(models.Enrollment).filter(
            models.Enrollment.grade == None
        ).delete()
        db.commit()
        system_logger.info(f"Cleared {result} expired enrollments")
        return {"message": f"已清理 {result} 条过期选课记录"}

    elif operation == "reset_course_counts":
        # 重置课程人数
        courses = db.query(models.Course).all()
        for course in courses:
            actual_count = len(course.enrollments)
            if course.current_students != actual_count:
                course.current_students = actual_count
                system_logger.warning(
                    f"Course {course.name} count mismatch: {course.current_students} -> {actual_count}"
                )
        db.commit()
        return {"message": "课程人数已重置"}

    raise HTTPException(status_code=400, detail="不支持的维护操作")

@router.get("/system/logs")
def get_system_logs(
    log_type: str = "system",
    lines: int = 100,
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以查看系统日志")

    log_file = f"logs/{datetime.now().strftime('%Y-%m-%d')}.log"
    try:
        with open(log_file, 'r') as f:
            logs = f.readlines()[-lines:]
        return {"logs": logs}
    except FileNotFoundError:
        return {"logs": []}