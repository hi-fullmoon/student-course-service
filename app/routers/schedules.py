from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..utils.auth import get_current_user
from ..utils.response import response

router = APIRouter()

@router.post("/")
def create_schedule(
    schedule: schemas.CourseScheduleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "teacher"]:
        return response(code=403, message="没有权限创建课程安排")

    # 检查课程是否存在
    course = db.query(models.Course).filter(models.Course.id == schedule.course_id).first()
    if not course:
        return response(code=404, message="课程不存在")

    # 如果是教师，检查是否是该课程的教师
    if current_user.role == "teacher" and course.teacher_id != current_user.id:
        return response(code=403, message="只能为自己的课程创建安排")

    # 检查教室是否存在
    classroom = db.query(models.Classroom).filter(models.Classroom.id == schedule.classroom_id).first()
    if not classroom:
        return response(code=404, message="教室不存在")

    # 检查时间冲突
    conflict = db.query(models.CourseSchedule).filter(
        models.CourseSchedule.classroom_id == schedule.classroom_id,
        models.CourseSchedule.day_of_week == schedule.day_of_week,
        models.CourseSchedule.start_time <= schedule.end_time,
        models.CourseSchedule.end_time >= schedule.start_time
    ).first()

    if conflict:
        return response(code=400, message="该时间段教室已被占用")

    db_schedule = models.CourseSchedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return response(data=db_schedule)

@router.get("/{schedule_id}")
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    schedule = db.query(models.CourseSchedule).filter(models.CourseSchedule.id == schedule_id).first()
    if not schedule:
        return response(code=404, message="课程安排不存在")
    return response(data=schedule)

@router.put("/{schedule_id}")
def update_schedule(
    schedule_id: int,
    schedule_update: schemas.CourseScheduleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "teacher"]:
        return response(code=403, message="没有权限修改课程安排")

    db_schedule = db.query(models.CourseSchedule).filter(models.CourseSchedule.id == schedule_id).first()
    if not db_schedule:
        return response(code=404, message="课程安排不存在")

    # 检查课程是否存在
    course = db.query(models.Course).filter(models.Course.id == schedule_update.course_id).first()
    if not course:
        return response(code=404, message="课程不存在")

    # 如果是教师，检查是否是该课程的教师
    if current_user.role == "teacher" and course.teacher_id != current_user.id:
        return response(code=403, message="只能修改自己课程的安排")

    # 检查教室是否存在
    classroom = db.query(models.Classroom).filter(models.Classroom.id == schedule_update.classroom_id).first()
    if not classroom:
        return response(code=404, message="教室不存在")

    # 检查时间冲突（排除当前记录）
    conflict = db.query(models.CourseSchedule).filter(
        models.CourseSchedule.id != schedule_id,
        models.CourseSchedule.classroom_id == schedule_update.classroom_id,
        models.CourseSchedule.day_of_week == schedule_update.day_of_week,
        models.CourseSchedule.start_time <= schedule_update.end_time,
        models.CourseSchedule.end_time >= schedule_update.start_time
    ).first()

    if conflict:
        return response(code=400, message="该时间段教室已被占用")

    for key, value in schedule_update.dict().items():
        setattr(db_schedule, key, value)

    db.commit()
    db.refresh(db_schedule)
    return response(data=db_schedule)

@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "teacher"]:
        return response(code=403, message="没有权限删除课程安排")

    db_schedule = db.query(models.CourseSchedule).filter(models.CourseSchedule.id == schedule_id).first()
    if not db_schedule:
        return response(code=404, message="课程安排不存在")

    # 如果是教师，检查是否是该课程的教师
    course = db.query(models.Course).filter(models.Course.id == db_schedule.course_id).first()
    if current_user.role == "teacher" and course.teacher_id != current_user.id:
        return response(code=403, message="只能删除自己课程的安排")

    db.delete(db_schedule)
    db.commit()
    return response(message="删除成功")

@router.get("/weekly")
def get_weekly_schedule(
    week_type: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.CourseSchedule)
    if week_type:
        query = query.filter(models.CourseSchedule.week_type == week_type)

    schedules = query.all()

    weekly_schedule = {}
    for schedule in schedules:
        course = db.query(models.Course).filter(models.Course.id == schedule.course_id).first()
        classroom = db.query(models.Classroom).filter(models.Classroom.id == schedule.classroom_id).first()

        if course and classroom:
            day = schedule.day_of_week
            if day not in weekly_schedule:
                weekly_schedule[day] = []

            schedule_info = {
                "course_name": course.name,
                "course_code": course.course_code,
                "classroom": f"{classroom.building}-{classroom.room_number}",
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "week_type": schedule.week_type
            }
            weekly_schedule[day].append(schedule_info)

    return response(data=weekly_schedule)