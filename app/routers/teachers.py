from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..utils.auth import get_current_user
from ..utils.response import response

router = APIRouter()

@router.get("/")
def get_teachers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    teachers = db.query(models.Teacher).offset(skip).limit(limit).all()
    return response(data=teachers)

@router.get("/{teacher_id}")
def get_teacher(
    teacher_id: int,
    db: Session = Depends(get_db)
):
    teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if not teacher:
        return response(code=404, message="教师不存在")
    return response(data=teacher)

@router.post("/")
def create_teacher(
    teacher: schemas.TeacherCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "admin":
        return response(code=403, message="没有权限创建教师")

    # 检查教师工号是否已存在
    existing_teacher = db.query(models.Teacher).filter(
        models.Teacher.teacher_id == teacher.teacher_id
    ).first()
    if existing_teacher:
        return response(code=400, message="教师工号已存在")

    db_teacher = models.Teacher(**teacher.dict())
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return response(data=db_teacher)

@router.put("/{teacher_id}")
def update_teacher(
    teacher_id: int,
    teacher_update: schemas.TeacherCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "admin":
        return response(code=403, message="没有权限修改教师信息")

    db_teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if not db_teacher:
        return response(code=404, message="教师不存在")

    # 检查更新的教师工号是否与其他教师冲突
    if teacher_update.teacher_id != db_teacher.teacher_id:
        existing_teacher = db.query(models.Teacher).filter(
            models.Teacher.teacher_id == teacher_update.teacher_id
        ).first()
        if existing_teacher:
            return response(code=400, message="教师工号已存在")

    for key, value in teacher_update.dict().items():
        setattr(db_teacher, key, value)

    db.commit()
    db.refresh(db_teacher)
    return response(data=db_teacher)

@router.delete("/{teacher_id}")
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "admin":
        return response(code=403, message="没有权限删除教师")

    db_teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if not db_teacher:
        return response(code=404, message="教师不存在")

    # 检查教师是否有关联的课程
    courses = db.query(models.Course).filter(models.Course.teacher_id == teacher_id).all()
    if courses:
        return response(code=400, message="该教师还有关联的课程，无法删除")

    db.delete(db_teacher)
    db.commit()
    return response(message="删除成功")

@router.get("/{teacher_id}/courses")
def get_teacher_courses(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if not teacher:
        return response(code=404, message="教师不存在")

    # 检查权限
    if current_user.role not in ["admin"] and (
        current_user.role != "teacher" or
        current_user.id != teacher_id
    ):
        return response(code=403, message="没有权限查看其他教师的课程")

    courses = db.query(models.Course).filter(models.Course.teacher_id == teacher_id).all()
    return response(data=courses)

@router.get("/{teacher_id}/schedule")
def get_teacher_schedule(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if not teacher:
        return response(code=404, message="教师不存在")

    # 获取教师的所有课程
    courses = db.query(models.Course).filter(models.Course.teacher_id == teacher_id).all()

    # 获取所有课程的课表
    schedules = []
    for course in courses:
        course_schedules = db.query(models.CourseSchedule).filter(
            models.CourseSchedule.course_id == course.id
        ).all()
        for schedule in course_schedules:
            schedule_data = {
                "course_name": course.name,
                "course_code": course.course_code,
                "day_of_week": schedule.day_of_week,
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "classroom": schedule.classroom.room_number,
                "building": schedule.classroom.building
            }
            schedules.append(schedule_data)

    return response(data=schedules)