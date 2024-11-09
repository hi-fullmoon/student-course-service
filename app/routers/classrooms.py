from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..utils.auth import get_current_user
from ..utils.response import response

router = APIRouter()

@router.get("/")
def get_classrooms(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    classrooms = db.query(models.Classroom).offset(skip).limit(limit).all()
    return response(data=classrooms)

@router.get("/{classroom_id}")
def get_classroom(
    classroom_id: int,
    db: Session = Depends(get_db)
):
    classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
    if not classroom:
        return response(code=404, message="教室不存在")
    return response(data=classroom)

@router.post("/")
def create_classroom(
    classroom: schemas.ClassroomCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "admin":
        return response(code=403, message="没有权限创建教室")

    # 检查教室编号是否已存在
    existing = db.query(models.Classroom).filter(
        models.Classroom.room_number == classroom.room_number,
        models.Classroom.building == classroom.building
    ).first()
    if existing:
        return response(code=400, message="该教室已存在")

    db_classroom = models.Classroom(**classroom.dict())
    db.add(db_classroom)
    db.commit()
    db.refresh(db_classroom)
    return response(data=db_classroom)

@router.put("/{classroom_id}")
def update_classroom(
    classroom_id: int,
    classroom_update: schemas.ClassroomCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "admin":
        return response(code=403, message="没有权限修改教室信息")

    db_classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
    if not db_classroom:
        return response(code=404, message="教室不存在")

    # 检查更新后的教室编号是否与其他教室冲突
    if (classroom_update.room_number != db_classroom.room_number or
        classroom_update.building != db_classroom.building):
        existing = db.query(models.Classroom).filter(
            models.Classroom.room_number == classroom_update.room_number,
            models.Classroom.building == classroom_update.building
        ).first()
        if existing:
            return response(code=400, message="该教室编号已存在")

    for key, value in classroom_update.dict().items():
        setattr(db_classroom, key, value)

    db.commit()
    db.refresh(db_classroom)
    return response(data=db_classroom)

@router.delete("/{classroom_id}")
def delete_classroom(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "admin":
        return response(code=403, message="没有权限删除教室")

    db_classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
    if not db_classroom:
        return response(code=404, message="教室不存在")

    # 检查是否有关联的课程安排
    schedules = db.query(models.CourseSchedule).filter(
        models.CourseSchedule.classroom_id == classroom_id
    ).first()
    if schedules:
        return response(code=400, message="该教室还有关联的课程安排，无法删除")

    db.delete(db_classroom)
    db.commit()
    return response(message="删除成功")

@router.get("/{classroom_id}/schedule")
def get_classroom_schedule(
    classroom_id: int,
    db: Session = Depends(get_db)
):
    classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
    if not classroom:
        return response(code=404, message="教室不存在")

    schedules = db.query(models.CourseSchedule).filter(
        models.CourseSchedule.classroom_id == classroom_id
    ).all()

    schedule_data = []
    for schedule in schedules:
        course = db.query(models.Course).filter(models.Course.id == schedule.course_id).first()
        if course:
            schedule_info = {
                "course_name": course.name,
                "course_code": course.course_code,
                "day_of_week": schedule.day_of_week,
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "week_type": schedule.week_type
            }
            schedule_data.append(schedule_info)

    return response(data=schedule_data)

@router.get("/available")
def get_available_classrooms(
    day_of_week: int,
    start_time: str,
    end_time: str,
    capacity_required: int = 0,
    db: Session = Depends(get_db)
):
    # 获取所有教室
    classrooms = db.query(models.Classroom)
    if capacity_required > 0:
        classrooms = classrooms.filter(models.Classroom.capacity >= capacity_required)

    classrooms = classrooms.all()
    available_rooms = []

    for classroom in classrooms:
        # 检查该时间段是否有课程安排
        conflict = db.query(models.CourseSchedule).filter(
            models.CourseSchedule.classroom_id == classroom.id,
            models.CourseSchedule.day_of_week == day_of_week,
            models.CourseSchedule.start_time <= end_time,
            models.CourseSchedule.end_time >= start_time
        ).first()

        if not conflict:
            available_rooms.append(classroom)

    return response(data=available_rooms)