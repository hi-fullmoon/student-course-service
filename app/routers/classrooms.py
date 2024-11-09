from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..utils.auth import get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.Classroom)
def create_classroom(
    classroom: schemas.ClassroomCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以添加教室")

    db_classroom = models.Classroom(**classroom.dict())
    db.add(db_classroom)
    db.commit()
    db.refresh(db_classroom)
    return db_classroom

@router.get("/", response_model=List[schemas.Classroom])
def read_classrooms(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    classrooms = db.query(models.Classroom).offset(skip).limit(limit).all()
    return classrooms

@router.get("/available", response_model=List[schemas.Classroom])
def get_available_classrooms(
    day: int,
    start_time: str,
    end_time: str,
    min_capacity: int = 0,
    need_projector: bool = False,
    need_computer: bool = False,
    db: Session = Depends(get_db)
):
    # 基本查询
    query = db.query(models.Classroom)

    # 设备需求
    if need_projector:
        query = query.filter(models.Classroom.has_projector == True)
    if need_computer:
        query = query.filter(models.Classroom.has_computer == True)

    # 容量需求
    if min_capacity > 0:
        query = query.filter(models.Classroom.capacity >= min_capacity)

    # 获取所有符合基本条件的教室
    classrooms = query.all()

    # 检查时间冲突
    available_classrooms = []
    for classroom in classrooms:
        # 检查该教室在指定时间段是否有课
        schedule_conflict = db.query(models.CourseSchedule).filter(
            models.CourseSchedule.classroom_id == classroom.id,
            models.CourseSchedule.day_of_week == day,
            models.CourseSchedule.start_time <= end_time,
            models.CourseSchedule.end_time >= start_time
        ).first()

        if not schedule_conflict:
            available_classrooms.append(classroom)

    return available_classrooms

@router.put("/{classroom_id}", response_model=schemas.Classroom)
def update_classroom(
    classroom_id: int,
    classroom_update: schemas.ClassroomCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以修改教室信息")

    db_classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
    if not db_classroom:
        raise HTTPException(status_code=404, detail="教室不存在")

    for key, value in classroom_update.dict().items():
        setattr(db_classroom, key, value)

    db.commit()
    db.refresh(db_classroom)
    return db_classroom

@router.delete("/{classroom_id}")
def delete_classroom(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以删除教室")

    db_classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
    if not db_classroom:
        raise HTTPException(status_code=404, detail="教室不存在")

    if len(db_classroom.course_schedules) > 0:
        raise HTTPException(status_code=400, detail="教室还有关��的课程，无法删除")

    db.delete(db_classroom)
    db.commit()
    return {"message": "教室删除成功"}