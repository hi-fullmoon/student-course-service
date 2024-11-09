from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import models
from ..utils.auth import get_current_user
from ..utils.response import response
from datetime import datetime

router = APIRouter()

@router.get("/course-statistics")
def get_course_statistics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "teacher"]:
        return response(code=403, message="没有权限查看课程统计")

    courses = db.query(models.Course).all()
    stats = []

    for course in courses:
        # 如果是教师，只能查看自己的课程
        if current_user.role == "teacher" and course.teacher_id != current_user.id:
            continue

        enrollments = course.enrollments
        total_students = len(enrollments)
        graded_students = len([e for e in enrollments if e.grade is not None])

        if graded_students > 0:
            avg_grade = sum(e.grade for e in enrollments if e.grade is not None) / graded_students
        else:
            avg_grade = 0

        course_stat = {
            "course_id": course.id,
            "course_name": course.name,
            "course_code": course.course_code,
            "teacher_name": course.teacher.name if course.teacher else "未分配",
            "total_students": total_students,
            "graded_students": graded_students,
            "average_grade": round(avg_grade, 2),
            "capacity_usage": f"{(total_students/course.max_students*100):.1f}%"
        }
        stats.append(course_stat)

    return response(data=stats)

@router.get("/student-performance")
def get_student_performance(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "teacher"]:
        return response(code=403, message="没有权限查看学生成绩统计")

    students = db.query(models.Student).all()
    performance = []

    for student in students:
        enrollments = student.enrollments
        total_courses = len(enrollments)
        completed_courses = len([e for e in enrollments if e.grade is not None])
        total_credits = sum(e.course.credit for e in enrollments if e.grade is not None)

        if completed_courses > 0:
            gpa = sum(e.grade * e.course.credit for e in enrollments if e.grade is not None) / total_credits
        else:
            gpa = 0

        student_perf = {
            "student_id": student.student_id,
            "name": student.name,
            "class_name": student.class_name,
            "total_courses": total_courses,
            "completed_courses": completed_courses,
            "total_credits": total_credits,
            "gpa": round(gpa/20, 2)  # 转换为5分制
        }
        performance.append(student_perf)

    return response(data=performance)

@router.get("/teacher-workload")
def get_teacher_workload(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "admin":
        return response(code=403, message="只有管理员可以查看教师工作量")

    teachers = db.query(models.Teacher).all()
    workload = []

    for teacher in teachers:
        courses = teacher.courses
        total_students = sum(course.current_students for course in courses)
        total_credits = sum(course.credit for course in courses)

        teacher_load = {
            "teacher_id": teacher.teacher_id,
            "name": teacher.name,
            "department": teacher.department,
            "title": teacher.title,
            "course_count": len(courses),
            "total_students": total_students,
            "total_credits": total_credits
        }
        workload.append(teacher_load)

    return response(data=workload)

@router.get("/classroom-usage")
def get_classroom_usage(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "admin":
        return response(code=403, message="只有管理员可以查看教室使用情况")

    classrooms = db.query(models.Classroom).all()
    usage_stats = []

    for classroom in classrooms:
        schedules = db.query(models.CourseSchedule).filter(
            models.CourseSchedule.classroom_id == classroom.id
        ).all()

        # 计算每周使用课时数
        total_hours = sum(
            (datetime.strptime(s.end_time, "%H:%M") -
             datetime.strptime(s.start_time, "%H:%M")).seconds / 3600
            for s in schedules
        )

        usage_stat = {
            "room_number": classroom.room_number,
            "building": classroom.building,
            "capacity": classroom.capacity,
            "weekly_hours": round(total_hours, 1),
            "schedule_count": len(schedules),
            "has_projector": classroom.has_projector,
            "has_computer": classroom.has_computer
        }
        usage_stats.append(usage_stat)

    return response(data=usage_stats)

@router.get("/enrollment-trends")
def get_enrollment_trends(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "teacher"]:
        return response(code=403, message="没有权限查看选课趋势")

    courses = db.query(models.Course).all()
    trends = []

    for course in courses:
        # 如果是教师，只能查看自己的课程
        if current_user.role == "teacher" and course.teacher_id != current_user.id:
            continue

        course_trend = {
            "course_id": course.id,
            "course_name": course.name,
            "course_code": course.course_code,
            "max_students": course.max_students,
            "current_students": course.current_students,
            "enrollment_rate": f"{(course.current_students/course.max_students*100):.1f}%",
            "remaining_seats": course.max_students - course.current_students
        }
        trends.append(course_trend)

    return response(data=trends)