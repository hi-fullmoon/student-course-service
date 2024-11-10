from datetime import time
from typing import List
from fastapi import APIRouter, HTTPException, Depends, Security
from sqlalchemy.orm import Session
from app.models import CourseScheduleModel, CourseModel, StudentCourseModel
from app.utils.init_db import get_db
from app.utils.auth import get_current_user
from app.utils.response import response_success, response_error
from pydantic import BaseModel

router = APIRouter()

class TimeSlot(BaseModel):
    start_time: time
    end_time: time
    weekday: int  # 0-6 表示周一到周日

class CourseScheduleCreate(BaseModel):
    course_id: int
    time_slots: List[TimeSlot]

def check_time_conflict(db: Session, schedule: CourseScheduleCreate, student_id: int):
    """检查学生的课程时间冲突，返回冲突信息"""
    # 获取学生已选课程的ID列表
    enrolled_courses = db.query(StudentCourseModel).filter(
        StudentCourseModel.student_id == student_id
    ).all()
    enrolled_course_ids = [ec.course_id for ec in enrolled_courses]

    conflicts = []
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    for slot in schedule.time_slots:
        # 检查学生在同一时间段是否有其他课程
        conflicting_schedules = db.query(CourseScheduleModel, CourseModel).join(
            CourseModel
        ).filter(
            CourseScheduleModel.course_id.in_(enrolled_course_ids),
            CourseScheduleModel.weekday == slot.weekday,
            CourseScheduleModel.start_time < slot.end_time,
            CourseScheduleModel.end_time > slot.start_time
        ).all()

        for conflict_schedule, conflict_course in conflicting_schedules:
            conflicts.append({
                "weekday": weekday_names[slot.weekday],
                "conflict_course_name": conflict_course.name,
                "conflict_time": f"{conflict_schedule.start_time.strftime('%H:%M')}-{conflict_schedule.end_time.strftime('%H:%M')}",
                "new_time": f"{slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}"
            })

    return conflicts

@router.post("/schedules")
async def create_course_schedule(
    schedule: CourseScheduleCreate,
    db: Session = Depends(get_db)
):
    # 验证课程是否存在
    course = db.query(CourseModel).filter(CourseModel.id == schedule.course_id).first()
    if not course:
        return response_error(code=404, message="课程不存在")

    # 检查课程是否已有时间安排
    existing_schedules = db.query(CourseScheduleModel).filter(
        CourseScheduleModel.course_id == schedule.course_id
    ).first()

    if existing_schedules:
        return response_error(message="该课程已有时间安排，请先删除现有安排后再创建新的时间安排")

    # 验证时间段
    for slot in schedule.time_slots:
        if slot.start_time >= slot.end_time:
            return response_error(message="开始时间必须早于结束时间")

        if slot.weekday < 0 or slot.weekday > 6:
            return response_error(message="无效的星期数")

    try:
        # 保存时间安排
        for slot in schedule.time_slots:
            schedule_model = CourseScheduleModel(
                course_id=schedule.course_id,
                weekday=slot.weekday,
                start_time=slot.start_time,
                end_time=slot.end_time
            )
            db.add(schedule_model)

        db.commit()

        response_data = {
            "time_slots": [{
                "weekday": slot.weekday,
                "start_time": slot.start_time.strftime("%H:%M"),
                "end_time": slot.end_time.strftime("%H:%M")
            } for slot in schedule.time_slots]
        }

        return response_success(
            message="课程时间安排创建成功",
            data=response_data
        )
    except Exception as e:
        db.rollback()
        return response_error(message=f"创建课程时间安排失败: {str(e)}")

@router.get("/schedules/{course_id}")
async def get_course_schedule(
    course_id: int,
    db: Session = Depends(get_db)
):
    schedules = db.query(CourseScheduleModel).filter(
        CourseScheduleModel.course_id == course_id
    ).all()

    if not schedules:
        return response_error(code=404, message="未找到课程时间安排")

    return response_success(data=[{
        "weekday": schedule.weekday,
        "start_time": schedule.start_time.strftime("%H:%M"),
        "end_time": schedule.end_time.strftime("%H:%M")
    } for schedule in schedules])

@router.get("/schedules/my")
async def get_my_schedules(
    db: Session = Depends(get_db),
    current_user = Security(get_current_user)
):
    # 获取学生选修的所有课程
    enrolled_courses = db.query(StudentCourseModel).filter(
        StudentCourseModel.student_id == current_user.id
    ).all()

    course_ids = [enrollment.course_id for enrollment in enrolled_courses]

    # 获取这些课程的时间安排
    schedules = db.query(CourseScheduleModel, CourseModel).join(
        CourseModel
    ).filter(
        CourseScheduleModel.course_id.in_(course_ids)
    ).all()

    schedule_data = [{
        "course_name": course.name,
        "weekday": schedule.weekday,
        "start_time": schedule.start_time.strftime("%H:%M"),
        "end_time": schedule.end_time.strftime("%H:%M")
    } for schedule, course in schedules]

    return response_success(data=schedule_data)

@router.put("/schedules/{course_id}")
async def update_course_schedule(
    course_id: int,
    schedule: CourseScheduleCreate,
    db: Session = Depends(get_db)
):
    # 验证课程是否存在
    course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
    if not course:
        return response_error(code=404, message="课程不存在")

    # 验证新的时间段
    for slot in schedule.time_slots:
        if slot.start_time >= slot.end_time:
            return response_error(message="开始时间必须早于结束时间")

        if slot.weekday < 0 or slot.weekday > 6:
            return response_error(message="无效的星期数")

    try:
        # 删除现有的时间安排
        db.query(CourseScheduleModel).filter(
            CourseScheduleModel.course_id == course_id
        ).delete()

        # 创建新的时间安排
        for slot in schedule.time_slots:
            schedule_model = CourseScheduleModel(
                course_id=course_id,
                weekday=slot.weekday,
                start_time=slot.start_time,
                end_time=slot.end_time
            )
            db.add(schedule_model)

        db.commit()

        response_data = {
            "time_slots": [{
                "weekday": slot.weekday,
                "start_time": slot.start_time.strftime("%H:%M"),
                "end_time": slot.end_time.strftime("%H:%M")
            } for slot in schedule.time_slots]
        }

        return response_success(
            message="课程时间安排更新成功",
            data=response_data
        )
    except Exception as e:
        db.rollback()
        return response_error(message=f"更新课程时间安排失败: {str(e)}")

@router.delete("/schedules/{course_id}")
async def delete_course_schedule(
    course_id: int,
    db: Session = Depends(get_db)
):
    # 验证课程是否存在
    course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
    if not course:
        return response_error(code=404, message="课程不存在")

    try:
        # 删除课程的所有时间安排
        deleted = db.query(CourseScheduleModel).filter(
            CourseScheduleModel.course_id == course_id
        ).delete()

        if deleted == 0:
            return response_error(message="该课程没有时间安排")

        db.commit()
        return response_success(message="课程时间安排删除成功")
    except Exception as e:
        db.rollback()
        return response_error(message=f"删除课程时间安排失败: {str(e)}")