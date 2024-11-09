from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..utils.auth import get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.Course)
def create_course(
    course: schemas.CourseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="没有权限创建课程")

    db_course = models.Course(**course.dict(), current_students=0)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@router.get("/", response_model=List[schemas.Course])
def read_courses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    courses = db.query(models.Course).offset(skip).limit(limit).all()
    return courses

@router.get("/{course_id}", response_model=schemas.Course)
def read_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    return course

@router.get("/{course_id}/students", response_model=List[schemas.Student])
def read_course_students(course_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    return [enrollment.student for enrollment in course.enrollments]

@router.put("/{course_id}", response_model=schemas.Course)
def update_course(
    course_id: int,
    course_update: schemas.CourseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="没有权限修改课程")

    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if db_course is None:
        raise HTTPException(status_code=404, detail="课程不存在")

    for key, value in course_update.dict().items():
        setattr(db_course, key, value)

    db.commit()
    db.refresh(db_course)
    return db_course

@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以删除课程")

    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if db_course is None:
        raise HTTPException(status_code=404, detail="课程不存在")

    if db_course.current_students > 0:
        raise HTTPException(status_code=400, detail="课程还有学生，无法删除")

    db.delete(db_course)
    db.commit()
    return {"message": "课程删除成功"}

@router.get("/search/", response_model=List[schemas.Course])
def search_courses(
    keyword: Optional[str] = None,
    teacher: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Course)

    if keyword:
        query = query.filter(
            (models.Course.name.contains(keyword)) |
            (models.Course.course_code.contains(keyword))
        )

    if teacher:
        query = query.filter(models.Course.teacher == teacher)

    return query.all()