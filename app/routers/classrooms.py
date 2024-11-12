from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import ClassroomModel
from app.schemas import Classroom, ClassroomCreate, ClassroomUpdate
from app.utils.init_db import get_db
from app.utils.response import model_to_dict, response_success

router = APIRouter()


@router.post("/classrooms", response_model=Classroom)
def create_classroom(classroom: ClassroomCreate, db: Session = Depends(get_db)):
    # 检查是否存在同名教室
    existing_classroom = (
        db.query(ClassroomModel).filter(ClassroomModel.name == classroom.name).first()
    )
    if existing_classroom:
        raise HTTPException(status_code=400, detail="教室名称已存在")

    db_classroom = ClassroomModel(**classroom.model_dump())
    db.add(db_classroom)
    db.commit()
    db.refresh(db_classroom)
    return response_success(data=model_to_dict(db_classroom))


@router.get("/classrooms", response_model=List[Classroom])
def get_classrooms(
    name: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(ClassroomModel)

    if name:
        query = query.filter(ClassroomModel.name.ilike(f"%{name}%"))

    classrooms = query.offset(skip).limit(limit).all()
    return response_success(data=[model_to_dict(classroom) for classroom in classrooms])


@router.get("/classrooms/{classroom_id}", response_model=Classroom)
def get_classroom(classroom_id: int, db: Session = Depends(get_db)):
    classroom = (
        db.query(ClassroomModel).filter(ClassroomModel.id == classroom_id).first()
    )
    if classroom is None:
        raise HTTPException(status_code=404, detail="教室不存在")
    return response_success(data=model_to_dict(classroom))


@router.put("/classrooms/{classroom_id}", response_model=Classroom)
def update_classroom(
    classroom_id: int, classroom: ClassroomUpdate, db: Session = Depends(get_db)
):
    db_classroom = (
        db.query(ClassroomModel).filter(ClassroomModel.id == classroom_id).first()
    )
    if db_classroom is None:
        raise HTTPException(status_code=404, detail="教室不存在")

    # 如果要更新名称，检查新名称是否与其他教室重复
    if classroom.name is not None and classroom.name != db_classroom.name:
        existing_classroom = (
            db.query(ClassroomModel)
            .filter(
                ClassroomModel.name == classroom.name, ClassroomModel.id != classroom_id
            )
            .first()
        )
        if existing_classroom:
            raise HTTPException(status_code=400, detail="教室名称已存在")

    update_data = classroom.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_classroom, field, value)

    db.commit()
    db.refresh(db_classroom)
    return response_success(data=model_to_dict(db_classroom))


@router.delete("/classrooms/{classroom_id}")
def delete_classroom(classroom_id: int, db: Session = Depends(get_db)):
    db_classroom = (
        db.query(ClassroomModel).filter(ClassroomModel.id == classroom_id).first()
    )
    if db_classroom is None:
        raise HTTPException(status_code=404, detail="教室不存在")

    db.delete(db_classroom)
    db.commit()
    return response_success(data={"message": "教室已删除"})
