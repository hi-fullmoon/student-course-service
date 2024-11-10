from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import timedelta
from app.utils.auth import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
from app.models import StudentModel
from app.utils.init_db import get_db
from app.utils.response import response_success, response_error
from app.schemas import LoginData

router = APIRouter()

@router.post("/login")
async def login(login_data: LoginData, db: Session = Depends(get_db)):
    student = db.query(StudentModel).filter(StudentModel.username == login_data.username).first()
    if not student or not verify_password(login_data.password, student.password):
        return response_error(message="用户名或密码错误")

    if not student.is_active:
        return response_error(message="该账号已被禁用")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": student.username}, expires_delta=access_token_expires
    )
    return response_success(data={
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": {
            "id": student.id,
            "username": student.username,
        }
    })

# 获取当前用户信息
@router.get("/current_user")
async def get_current_user(current_user: StudentModel = Depends(get_current_user)):
    return response_success(data={
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "gender": current_user.gender,
        "student_number": current_user.student_number,
        "class_name": current_user.class_name,
        "enrollment_date": current_user.enrollment_date.isoformat() if current_user.enrollment_date else None
    })
