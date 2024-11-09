from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import models
from ..utils.auth import get_current_active_user
from ..utils.reports import create_excel_report, create_word_report

router = APIRouter()

@router.get("/course/{course_id}/excel")
def export_course_report(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="没有权限导出报表")

    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    # 准备数据
    data = []
    for enrollment in course.enrollments:
        data.append({
            "学生ID": enrollment.student.student_id,
            "学生姓名": enrollment.student.name,
            "班级": enrollment.student.class_name,
            "成绩": enrollment.grade if enrollment.grade else "未评分"
        })

    return create_excel_report(data, f"{course.name}_成绩表.xlsx")

@router.get("/student/{student_id}/transcript")
def export_student_transcript(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role == "student" and current_user.student_id != student_id:
        raise HTTPException(status_code=403, detail="只能导出自己的成绩单")

    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 准备数据
    content = [{
        "学生信息": "",
        "学号": student.student_id,
        "姓名": student.name,
        "班级": student.class_name
    }]

    course_data = []
    total_credits = 0
    total_grade_points = 0
    graded_courses = 0

    for enrollment in student.enrollments:
        if enrollment.grade is not None:
            grade_point = (enrollment.grade / 20) - 1  # 简单的绩点计算方式
            total_grade_points += grade_point * enrollment.course.credit
            total_credits += enrollment.course.credit
            graded_courses += 1

        course_data.append({
            "课程编号": enrollment.course.course_code,
            "课程名称": enrollment.course.name,
            "学分": enrollment.course.credit,
            "成绩": enrollment.grade if enrollment.grade else "未评分",
            "任课教师": enrollment.course.teacher
        })

    content.extend(course_data)

    if graded_courses > 0:
        gpa = total_grade_points / total_credits
        content.append({
            "总结": "",
            "总学分": total_credits,
            "平均绩点": round(gpa, 2)
        })

    return create_word_report(
        f"{student.name}的成绩单",
        content,
        f"{student.name}_成绩单.docx"
    )

@router.get("/statistics/department")
def export_department_statistics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="没有权限导出系统统计报表")

    # 准备课程统计数据
    courses = db.query(models.Course).all()
    course_stats = []

    for course in courses:
        enrollments = course.enrollments
        total_students = len(enrollments)
        graded_students = len([e for e in enrollments if e.grade is not None])

        if graded_students > 0:
            avg_grade = sum(e.grade for e in enrollments if e.grade is not None) / graded_students
        else:
            avg_grade = 0

        course_stats.append({
            "课程编号": course.course_code,
            "课程名称": course.name,
            "教师": course.teacher,
            "选课人数": total_students,
            "已评分人数": graded_students,
            "平均分": round(avg_grade, 2),
            "剩余名额": course.max_students - course.current_students
        })

    return create_excel_report(course_stats, "课程统计报表.xlsx")