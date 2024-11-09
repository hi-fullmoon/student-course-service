from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..utils.auth import get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.Enrollment)
def create_enrollment(
    enrollment: schemas.EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # 检查权限
    if current_user.role == "student":
        if current_user.student_id != enrollment.student_id:
            raise HTTPException(status_code=403, detail="只能为自己选课")
    elif current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="没有选课权限")

    # 检查学生是否存在
    student = db.query(models.Student).filter(models.Student.id == enrollment.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 检查课程是否存在
    course = db.query(models.Course).filter(models.Course.id == enrollment.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    # 检查是否已经选过这门课
    existing_enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == enrollment.student_id,
        models.Enrollment.course_id == enrollment.course_id
    ).first()
    if existing_enrollment:
        raise HTTPException(status_code=400, detail="已经选过这门课程")

    # 检查课程是否已满
    if course.current_students >= course.max_students:
        raise HTTPException(status_code=400, detail="课程已满")

    # 创建选课记录
    db_enrollment = models.Enrollment(**enrollment.dict())
    db.add(db_enrollment)

    # 更新课程当前学生数
    course.current_students += 1

    db.commit()
    db.refresh(db_enrollment)
    return db_enrollment

@router.delete("/{enrollment_id}")
def delete_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="选课记录不存在")

    # 检查权限
    if current_user.role == "student":
        if current_user.student_id != enrollment.student_id:
            raise HTTPException(status_code=403, detail="只能退自己的课")
    elif current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="没有退课权限")

    # 更新课程当前学生数
    course = db.query(models.Course).filter(models.Course.id == enrollment.course_id).first()
    course.current_students -= 1

    db.delete(enrollment)
    db.commit()
    return {"message": "退课成功"}

@router.put("/{enrollment_id}/grade")
def update_grade(
    enrollment_id: int,
    grade: float,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="只有教师和管理员可以录入成绩")

    enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="选课记录不存在")

    if grade < 0 or grade > 100:
        raise HTTPException(status_code=400, detail="成绩必须在0-100之间")

    enrollment.grade = grade
    db.commit()
    return {"message": "成绩更新成功"}

@router.get("/student/{student_id}", response_model=List[schemas.Course])
def get_student_courses(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # 检查权限
    if current_user.role == "student":
        if current_user.student_id != student_id:
            raise HTTPException(status_code=403, detail="只能查看自己的选课记录")

    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    return [enrollment.course for enrollment in student.enrollments]

@router.get("/statistics/course/{course_id}")
def get_course_statistics(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="没有权限查看统计信息")

    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    enrollments = course.enrollments
    total_students = len(enrollments)
    graded_students = len([e for e in enrollments if e.grade is not None])

    if graded_students > 0:
        average_grade = sum(e.grade for e in enrollments if e.grade is not None) / graded_students
        max_grade = max((e.grade for e in enrollments if e.grade is not None), default=0)
        min_grade = min((e.grade for e in enrollments if e.grade is not None), default=0)
    else:
        average_grade = 0
        max_grade = 0
        min_grade = 0

    return {
        "course_name": course.name,
        "total_students": total_students,
        "graded_students": graded_students,
        "average_grade": round(average_grade, 2),
        "max_grade": max_grade,
        "min_grade": min_grade,
        "available_seats": course.max_students - course.current_students
    }

@router.get("/statistics/student/{student_id}")
def get_student_statistics(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role == "student" and current_user.student_id != student_id:
        raise HTTPException(status_code=403, detail="只能查看自己的统计信息")

    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    enrollments = student.enrollments
    total_courses = len(enrollments)
    graded_courses = len([e for e in enrollments if e.grade is not None])
    total_credits = sum(e.course.credit for e in enrollments)

    if graded_courses > 0:
        average_grade = sum(e.grade for e in enrollments if e.grade is not None) / graded_courses
    else:
        average_grade = 0

    return {
        "student_name": student.name,
        "total_courses": total_courses,
        "graded_courses": graded_courses,
        "total_credits": total_credits,
        "average_grade": round(average_grade, 2),
        "courses_in_progress": total_courses - graded_courses
    }

@router.post("/batch", response_model=dict)
def batch_enrollment(
    batch: schemas.BatchEnrollment,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="没有权限进行批量选课")

    course = db.query(models.Course).filter(models.Course.id == batch.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    results = {"success": [], "failed": []}

    for student_id in batch.student_ids:
        try:
            # 检查学生是否存在
            student = db.query(models.Student).filter(models.Student.id == student_id).first()
            if not student:
                results["failed"].append({"student_id": student_id, "reason": "学生不存在"})
                continue

            # 检查是否已选课
            existing = db.query(models.Enrollment).filter(
                models.Enrollment.student_id == student_id,
                models.Enrollment.course_id == batch.course_id
            ).first()

            if existing:
                results["failed"].append({"student_id": student_id, "reason": "已经选过这门课"})
                continue

            # 检查课程容量
            if course.current_students >= course.max_students:
                results["failed"].append({"student_id": student_id, "reason": "课程已满"})
                continue

            # 创建选课记录
            enrollment = models.Enrollment(student_id=student_id, course_id=batch.course_id)
            db.add(enrollment)
            course.current_students += 1
            results["success"].append(student_id)

        except Exception as e:
            results["failed"].append({"student_id": student_id, "reason": str(e)})

    db.commit()
    return results