from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.models import StudentCourseModel
from app.utils.init_db import get_db
from app.schemas import Schedule
from app.utils.response import response_success, response_error

router = APIRouter()

@router.get("/schedules/{student_id}")
def get_student_schedule(student_id: int, db: Session = Depends(get_db)):
    schedule = db.query(StudentCourseModel).filter(
        StudentCourseModel.student_id == student_id
    ).all()
    if not schedule:
        return response_error(code=404, message="未找到该学生的课程表")
    return response_success(data=schedule)