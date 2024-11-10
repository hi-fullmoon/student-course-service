from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from sqlalchemy.orm import Session
from app.models import StudentModel
from app.schemas import StudentCreate, StudentUpdate
from app.utils.auth import get_current_user
from app.utils.response import response_success
from app.utils.init_db import get_db
from datetime import datetime, timezone
from sqlalchemy import and_

router = APIRouter()

@router.post("/students")
async def create_student(
    student: StudentCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查权限（只有管理员可以创建学生）
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="没有权限执行此操作")

    # 检查用户名是否已存在
    existing_student = db.query(StudentModel).filter(
        StudentModel.username == student.username
    ).first()
    if existing_student:
        raise HTTPException(status_code=400, detail="该用户名已存在")

    # 检查邮箱是否已存在
    if student.email:
        existing_email = db.query(StudentModel).filter(
            StudentModel.email == student.email
        ).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="该邮箱已被使用")

    # 生成学号
    student_number = StudentModel.generate_student_number(db)

    # 创建新学生
    new_student = StudentModel(
        username=student.username,
        student_number=student_number,  # 使用生成的学号
        email=student.email,
        gender=student.gender,
        class_name=student.class_name,
        enrollment_date=student.enrollment_date or datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return response_success(data={
        "id": new_student.id,
        "student_number": new_student.student_number
    })

@router.get("/students")
async def list_students(
    username: str = Query(default=None, description="用户名模糊搜索"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查权限
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="没有权限执行此操作")

    # 构建查询
    query = db.query(StudentModel).filter(StudentModel.username != "admin")

    # 如果提供了username参数，添加模糊查询条件
    if username:
        query = query.filter(StudentModel.username.like(f"%{username}%"))

    students = query.all()

    return response_success(data=[{
        "id": student.id,
        "username": student.username,
        "email": student.email,
        "gender": student.gender,
        "student_number": student.student_number,
        "class_name": student.class_name,
        "enrollment_date": student.enrollment_date.isoformat() if student.enrollment_date else None
    } for student in students])

@router.get("/students/{student_id}")
async def get_student(
    student_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查权限
    if current_user.username != "admin" and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="没有权限执行此操作")

    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    return response_success(data={
        "id": student.id,
        "username": student.username,
        "email": student.email,
        "gender": student.gender,
        "is_active": student.is_active
    })

@router.put("/students/{student_id}")
async def update_student(
    student_id: int,
    student_update: StudentUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查权限
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="没有权限执行此操作")

    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 检查邮箱是否已被其他用户使用
    if student_update.email:
        existing_email = db.query(StudentModel).filter(
            and_(
                StudentModel.email == student_update.email,
                StudentModel.id != student_id
            )
        ).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="该邮箱已被使用")

    # 更新学生信息
    update_data = student_update.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        for key, value in update_data.items():
            setattr(student, key, value)
        db.commit()

    return response_success()

@router.delete("/students/{student_id}")
async def delete_student(
    student_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查权限
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="没有权限执行此操作")

    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 物理删除学生记录
    db.delete(student)
    db.commit()

    return response_success()