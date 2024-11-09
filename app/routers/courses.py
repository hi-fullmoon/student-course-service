from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..utils.auth import get_current_user
from ..utils.response import response

router = APIRouter()

@router.get("/")
def get_courses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    courses = db.query(models.Course).offset(skip).limit(limit).all()
    return response(data=courses)

@router.get("/{course_id}")
def get_course(
    course_id: int,
    db: Session = Depends(get_db)
):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        return response(code=404, message="课程不存在")
    return response(data=course)

@router.post("/")
def create_course(
    course: schemas.CourseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "teacher"]:
        return response(code=403, message="没有权限创建课程")

    db_course = models.Course(**course.dict(), current_students=0)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return response(data=db_course)

@router.put("/{course_id}")
def update_course(
    course_id: int,
    course_update: schemas.CourseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "teacher"]:
        return response(code=403, message="没有权限修改课程")

    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not db_course:
        return response(code=404, message="课程不存在")

    # 检查是否为课程的教师
    if current_user.role == "teacher" and db_course.teacher_id != current_user.id:
        return response(code=403, message="只能修改自己的课程")

    for key, value in course_update.dict().items():
        setattr(db_course, key, value)

    db.commit()
    db.refresh(db_course)
    return response(data=db_course)

@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "teacher"]:
        return response(code=403, message="没有权限删除课程")

    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not db_course:
        return response(code=404, message="课程不存在")

    # 检查是否为课程的教师
    if current_user.role == "teacher" and db_course.teacher_id != current_user.id:
        return response(code=403, message="只能删除自己的课程")

    db.delete(db_course)
    db.commit()
    return response(message="删除成功")

@router.get("/{course_id}/students")
def get_course_students(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "teacher"]:
        return response(code=403, message="没有权限查看选课学生")

    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        return response(code=404, message="课程不存在")

    # 检查是否为课程的教师
    if current_user.role == "teacher" and course.teacher_id != current_user.id:
        return response(code=403, message="只能查看自己课程的学生")

    enrollments = db.query(models.Enrollment).filter(
        models.Enrollment.course_id == course_id
    ).all()

    students = []
    for enrollment in enrollments:
        student = db.query(models.Student).filter(
            models.Student.id == enrollment.student_id
        ).first()
        if student:
            student_data = {
                "id": student.id,
                "name": student.name,
                "student_id": student.student_id,
                "class_name": student.class_name,
                "grade": enrollment.grade
            }
            students.append(student_data)

    return response(data=students)

@router.get("/{course_id}/schedule")
def get_course_schedule(
    course_id: int,
    db: Session = Depends(get_db)
):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        return response(code=404, message="课程不存在")

    schedules = db.query(models.CourseSchedule).filter(
        models.CourseSchedule.course_id == course_id
    ).all()

    return response(data=schedules)