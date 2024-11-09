from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..utils.auth import get_current_active_user

router = APIRouter()

def validate_time_format(time_str: str) -> bool:
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def check_time_conflict(
    db: Session,
    classroom_id: int,
    day_of_week: int,
    start_time: str,
    end_time: str,
    week_type: str,
    exclude_schedule_id: int = None
) -> bool:
    query = db.query(models.CourseSchedule).filter(
        models.CourseSchedule.classroom_id == classroom_id,
        models.CourseSchedule.day_of_week == day_of_week,
        models.CourseSchedule.start_time <= end_time,
        models.CourseSchedule.end_time >= start_time
    )

    if exclude_schedule_id:
        query = query.filter(models.CourseSchedule.id != exclude_schedule_id)

    existing_schedule = query.first()
    return existing_schedule is not None

@router.post("/", response_model=schemas.CourseSchedule)
def create_schedule(
    schedule: schemas.CourseScheduleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="没有权限创建课程时间表")

    # 验证时间格式
    if not validate_time_format(schedule.start_time) or not validate_time_format(schedule.end_time):
        raise HTTPException(status_code=400, detail="时间格式错误，请使用HH:MM格式")

    # 验证星期
    if not 1 <= schedule.day_of_week <= 7:
        raise HTTPException(status_code=400, detail="星期必须在1-7之间")

    # 验证周类型
    if schedule.week_type not in ["all", "odd", "even"]:
        raise HTTPException(status_code=400, detail="周类型必须是 all, odd 或 even")

    # 检查课程是否存在
    course = db.query(models.Course).filter(models.Course.id == schedule.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    # 检查教室是否存在
    classroom = db.query(models.Classroom).filter(models.Classroom.id == schedule.classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")

    # 检查时间冲突
    if check_time_conflict(
        db,
        schedule.classroom_id,
        schedule.day_of_week,
        schedule.start_time,
        schedule.end_time,
        schedule.week_type
    ):
        raise HTTPException(status_code=400, detail="该时间段教室已被占用")

    db_schedule = models.CourseSchedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@router.get("/course/{course_id}", response_model=List[schemas.CourseSchedule])
def get_course_schedules(course_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    return course.schedules

@router.get("/classroom/{classroom_id}", response_model=List[schemas.CourseSchedule])
def get_classroom_schedules(classroom_id: int, db: Session = Depends(get_db)):
    classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    return classroom.course_schedules

@router.put("/{schedule_id}", response_model=schemas.CourseSchedule)
def update_schedule(
    schedule_id: int,
    schedule_update: schemas.CourseScheduleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="没有权限修改课程时间表")

    db_schedule = db.query(models.CourseSchedule).filter(models.CourseSchedule.id == schedule_id).first()
    if not db_schedule:
        raise HTTPException(status_code=404, detail="课程时间表不存在")

    # 验证时间格式和其他检查（与创建时相同）
    if not validate_time_format(schedule_update.start_time) or not validate_time_format(schedule_update.end_time):
        raise HTTPException(status_code=400, detail="时间格式错误，请使用HH:MM格式")

    if not 1 <= schedule_update.day_of_week <= 7:
        raise HTTPException(status_code=400, detail="星期必须在1-7之间")

    if schedule_update.week_type not in ["all", "odd", "even"]:
        raise HTTPException(status_code=400, detail="周类型必须是 all, odd 或 even")

    # 检查时间冲突（排除当前时间表）
    if check_time_conflict(
        db,
        schedule_update.classroom_id,
        schedule_update.day_of_week,
        schedule_update.start_time,
        schedule_update.end_time,
        schedule_update.week_type,
        schedule_id
    ):
        raise HTTPException(status_code=400, detail="该时间段教室已被占用")

    for key, value in schedule_update.dict().items():
        setattr(db_schedule, key, value)

    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="没有权限删除课程时间表")

    db_schedule = db.query(models.CourseSchedule).filter(models.CourseSchedule.id == schedule_id).first()
    if not db_schedule:
        raise HTTPException(status_code=404, detail="课程时间表不存在")

    db.delete(db_schedule)
    db.commit()
    return {"message": "课程时间表删除成功"}