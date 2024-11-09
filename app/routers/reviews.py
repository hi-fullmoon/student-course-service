from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..utils.auth import get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.CourseReview)
def create_review(
    review: schemas.CourseReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # 检查评分范围
    if not 1 <= review.rating <= 5:
        raise HTTPException(status_code=400, detail="评分必须在1-5之间")

    # 检查选课记录
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.id == review.enrollment_id
    ).first()

    if not enrollment:
        raise HTTPException(status_code=404, detail="选课记录不存在")

    # 检查是否是本人的选课记录
    if current_user.role == "student" and current_user.student_id != enrollment.student_id:
        raise HTTPException(status_code=403, detail="只能评价自己的课程")

    # 检查��否已经评价过
    if enrollment.review:
        raise HTTPException(status_code=400, detail="已经评价过这门课程")

    # 检查是否已有成绩
    if not enrollment.grade:
        raise HTTPException(status_code=400, detail="课程还未评分，无法评价")

    db_review = models.CourseReview(**review.dict())
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

@router.get("/course/{course_id}", response_model=List[schemas.CourseReview])
def get_course_reviews(course_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    reviews = db.query(models.CourseReview).join(
        models.Enrollment
    ).filter(
        models.Enrollment.course_id == course_id
    ).all()

    return reviews

@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    review = db.query(models.CourseReview).filter(models.CourseReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="评价不存在")

    if current_user.role == "student":
        if current_user.student_id != review.enrollment.student_id:
            raise HTTPException(status_code=403, detail="只能删除自己的评价")
    elif current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="没有权限删除评价")

    db.delete(review)
    db.commit()
    return {"message": "评价删除成功"}