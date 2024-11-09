from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..utils.auth import (
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..utils.response import response

router = APIRouter()

@router.post("/register")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        return response(code=400, message="用户名已被注册")

    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        return response(code=400, message="邮箱已被注册")

    db_user = models.User(
        username=user.username,
        email=user.email,
        password=user.password,
        role=user.role,
        student_id=user.student_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return response(data={
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "role": db_user.role
    })

@router.post("/login")
async def login(
    form_data: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or form_data.password != user.password:
        return response(code=401, message="用户名或密码错误")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return response(data={
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "student_id": user.student_id
        }
    })