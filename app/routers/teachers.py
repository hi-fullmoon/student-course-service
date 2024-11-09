from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..utils.auth import get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.Teacher)
def create_teacher(
    teacher: schemas.TeacherCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以添加教师")

    db_teacher = models.Teacher(**teacher.dict())
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher

@router.get("/", response_model=List[schemas.Teacher])
def read_teachers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    teachers = db.query(models.Teacher).offset(skip).limit(limit).all()
    return teachers

@router.get("/{teacher_id}", response_model=schemas.Teacher)
def read_teacher(
    teacher_id: int,
    db: Session = Depends(get_db)
):
    teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if teacher is None:
        raise HTTPException(status_code=404, detail="教师不存在")
    return teacher

@router.get("/{teacher_id}/courses", response_model=List[schemas.Course])
def read_teacher_courses(
    teacher_id: int,
    db: Session = Depends(get_db)
):
    teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if teacher is None:
        raise HTTPException(status_code=404, detail="教师不存在")
    return teacher.courses

@router.put("/{teacher_id}", response_model=schemas.Teacher)
def update_teacher(
    teacher_id: int,
    teacher_update: schemas.TeacherCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以修改教师信息")

    teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if teacher is None:
        raise HTTPException(status_code=404, detail="教师不存在")

    for key, value in teacher_update.dict().items():
        setattr(teacher, key, value)

    db.commit()
    db.refresh(teacher)
    return teacher

@router.delete("/{teacher_id}")
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以删除教师")

    teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if teacher is None:
        raise HTTPException(status_code=404, detail="教师不存在")

    if len(teacher.courses) > 0:
        raise HTTPException(status_code=400, detail="教师还有关联的课程，无法删除")

    db.delete(teacher)
    db.commit()
    return {"message": "教师删除成功"}