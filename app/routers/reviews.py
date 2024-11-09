from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..utils.auth import get_current_user
from ..utils.response import response

router = APIRouter()

@router.post("/")
def create_review(
    review: schemas.CourseReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 检查选课记录是否存在
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.id == review.enrollment_id
    ).first()
    if not enrollment:
        return response(code=404, message="选课记录不存在")

    # 检查是否是本人的选课记录
    if current_user.role == "student" and current_user.student_id != enrollment.student_id:
        return response(code=403, message="只能评价自己的课程")

    # 检查是否已经评价过
    existing_review = db.query(models.CourseReview).filter(
        models.CourseReview.enrollment_id == review.enrollment_id
    ).first()
    if existing_review:
        return response(code=400, message="已经评价过这门课程")

    # 检查评分范围
    if review.rating < 1 or review.rating > 5:
        return response(code=400, message="评分必须在1-5之间")

    db_review = models.CourseReview(**review.dict())
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return response(data=db_review)

@router.get("/course/{course_id}")
def get_course_reviews(
    course_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # 检查课程是否存在
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        return response(code=404, message="课程不存在")

    # 获取课程的所有评价
    reviews = []
    enrollments = db.query(models.Enrollment).filter(
        models.Enrollment.course_id == course_id
    ).all()

    for enrollment in enrollments:
        review = db.query(models.CourseReview).filter(
            models.CourseReview.enrollment_id == enrollment.id
        ).first()
        if review:
            review_data = {
                "id": review.id,
                "content": review.content,
                "rating": review.rating,
                "created_at": review.created_at,
                "student": None if review.is_anonymous else {
                    "id": enrollment.student.id,
                    "name": enrollment.student.name
                }
            }
            reviews.append(review_data)

    # 计算平均评分
    if reviews:
        avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
    else:
        avg_rating = 0

    return response(data={
        "reviews": reviews[skip:skip + limit],
        "total": len(reviews),
        "average_rating": round(avg_rating, 1)
    })

@router.put("/{review_id}")
def update_review(
    review_id: int,
    review_update: schemas.CourseReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_review = db.query(models.CourseReview).filter(models.CourseReview.id == review_id).first()
    if not db_review:
        return response(code=404, message="评价不存在")

    # 检查是否是本人的评价
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.id == db_review.enrollment_id
    ).first()
    if current_user.role == "student" and current_user.student_id != enrollment.student_id:
        return response(code=403, message="只能修改自己的评价")

    # 检查评分范围
    if review_update.rating < 1 or review_update.rating > 5:
        return response(code=400, message="评分必须在1-5之间")

    for key, value in review_update.dict().items():
        setattr(db_review, key, value)

    db.commit()
    db.refresh(db_review)
    return response(data=db_review)

@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_review = db.query(models.CourseReview).filter(models.CourseReview.id == review_id).first()
    if not db_review:
        return response(code=404, message="评价不存在")

    # 检查权限
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.id == db_review.enrollment_id
    ).first()
    if current_user.role == "student":
        if current_user.student_id != enrollment.student_id:
            return response(code=403, message="只能删除自己的评价")
    elif current_user.role not in ["admin"]:
        return response(code=403, message="没有权限删除评价")

    db.delete(db_review)
    db.commit()
    return response(message="删除成功")

@router.get("/statistics/course/{course_id}")
def get_course_review_statistics(
    course_id: int,
    db: Session = Depends(get_db)
):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        return response(code=404, message="课程不存在")

    reviews = []
    enrollments = db.query(models.Enrollment).filter(
        models.Enrollment.course_id == course_id
    ).all()

    for enrollment in enrollments:
        review = db.query(models.CourseReview).filter(
            models.CourseReview.enrollment_id == enrollment.id
        ).first()
        if review:
            reviews.append(review)

    if not reviews:
        return response(data={
            "total_reviews": 0,
            "average_rating": 0,
            "rating_distribution": {str(i): 0 for i in range(1, 6)}
        })

    # 计算评分分布
    rating_distribution = {str(i): 0 for i in range(1, 6)}
    for review in reviews:
        rating_distribution[str(review.rating)] += 1

    stats = {
        "total_reviews": len(reviews),
        "average_rating": round(sum(r.rating for r in reviews) / len(reviews), 1),
        "rating_distribution": rating_distribution
    }

    return response(data=stats)