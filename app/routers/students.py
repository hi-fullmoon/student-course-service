from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..utils.auth import get_current_user
from ..utils.response import response

router = APIRouter()

@router.get("/")
def get_students(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "teacher"]:
        return response(code=403, message="没有权限访问")

    students = db.query(models.Student).offset(skip).limit(limit).all()
    return response(data=students)

@router.get("/{student_id}")
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        return response(code=404, message="学生不存在")
    return response(data=student)

@router.post("/")
def create_student(
    student: schemas.StudentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "admin":
        return response(code=403, message="没有权限创建学生")

    db_student = models.Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return response(data=db_student)

@router.put("/{student_id}")
def update_student(
    student_id: int,
    student_update: schemas.StudentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "admin":
        return response(code=403, message="没有权限修改学生信息")

    db_student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not db_student:
        return response(code=404, message="学生不存在")

    for key, value in student_update.dict().items():
        setattr(db_student, key, value)

    db.commit()
    db.refresh(db_student)
    return response(data=db_student)

@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "admin":
        return response(code=403, message="没有权限删除学生")

    db_student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not db_student:
        return response(code=404, message="学生不存在")

    db.delete(db_student)
    db.commit()
    return response(message="删除成功")

@router.get("/{student_id}/courses")
def get_student_courses(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        return response(code=404, message="学生不存在")

    if current_user.role not in ["admin", "teacher"] and current_user.student_id != student_id:
        return response(code=403, message="没有权限查看其他学生的课程")

    enrollments = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == student_id
    ).all()

    courses = []
    for enrollment in enrollments:
        course = db.query(models.Course).filter(
            models.Course.id == enrollment.course_id
        ).first()
        if course:
            course_data = {
                "id": course.id,
                "name": course.name,
                "credit": course.credit,
                "grade": enrollment.grade
            }
            courses.append(course_data)

    return response(data=courses)