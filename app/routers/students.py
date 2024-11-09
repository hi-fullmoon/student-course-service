from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..utils.auth import get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.Student)
def create_student(
    student: schemas.StudentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以创建学生账号")

    db_student = models.Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@router.get("/", response_model=List[schemas.Student])
def read_students(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="没有权限查看所有学生信息")
    students = db.query(models.Student).offset(skip).limit(limit).all()
    return students

@router.get("/me", response_model=schemas.Student)
def read_own_info(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="非学生用户")
    if not current_user.student_id:
        raise HTTPException(status_code=404, detail="未关联学生信息")

    student = db.query(models.Student).filter(models.Student.id == current_user.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生信息不存在")
    return student

@router.get("/{student_id}", response_model=schemas.Student)
def read_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role == "student" and current_user.student_id != student_id:
        raise HTTPException(status_code=403, detail="只能查看自己的信息")

    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    return student