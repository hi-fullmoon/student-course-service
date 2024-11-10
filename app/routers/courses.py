from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.models import CourseModel, StudentCourseModel, StudentModel
from app.schemas import CourseCreate
from app.utils.init_db import get_db
from app.utils.auth import oauth2_scheme
from app.utils.response import response_success, response_error

router = APIRouter()

@router.post("/courses")
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    try:
        db_course = CourseModel(**course.dict())
        db.add(db_course)
        db.commit()
        db.refresh(db_course)
        return response_success(data=db_course)
    except Exception as e:
        return response_error(message=f"创建课程失败: {str(e)}")

@router.get("/courses")
def get_courses(db: Session = Depends(get_db)):
    courses = db.query(CourseModel).all()
    return response_success(data=courses)

@router.get("/courses/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
    if not course:
        return response_error(code=404, message="课程不存在")
    return response_success(data=course)

@router.post("/courses/{course_id}/enroll")
def enroll_course(course_id: int, student_id: int, db: Session = Depends(get_db)):
    # 检查课程是否存在
    course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
    if not course:
        return response_error(code=404, message="课程不存在")

    # 检查学生是否已经选择该课程
    existing_enrollment = db.query(StudentCourseModel).filter(
        StudentCourseModel.student_id == student_id,
        StudentCourseModel.course_id == course_id
    ).first()

    if existing_enrollment:
        return response_error(message="已经选择了该课程")

    # 检查课程是否已满
    current_students = db.query(StudentCourseModel).filter(
        StudentCourseModel.course_id == course_id
    ).count()

    if current_students >= course.max_student_num:
        return response_error(message="课程已满")

    try:
        # 创建选课记录
        new_enrollment = StudentCourseModel(
            student_id=student_id,
            course_id=course_id
        )
        db.add(new_enrollment)
        db.commit()
        return response_success(message="选课成功")
    except Exception as e:
        return response_error(message=f"选课失败: {str(e)}")