from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session

from app.models import (
    ClassroomModel,
    CourseModel,
    CourseScheduleModel,
    StudentCourseModel,
)
from app.schemas import CourseScheduleCreate
from app.utils.auth import get_current_user
from app.utils.init_db import get_db
from app.utils.response import response_error, response_success

router = APIRouter()


def check_time_conflict(db: Session, schedule: CourseScheduleCreate, student_id: int):
    """检查学生的课程时间冲突，返回冲突信息"""
    # 获取学生已选课程的ID列表
    enrolled_courses = (
        db.query(StudentCourseModel)
        .filter(StudentCourseModel.student_id == student_id)
        .all()
    )
    enrolled_course_ids = [ec.course_id for ec in enrolled_courses]

    conflicts = []
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    for slot in schedule.time_slots:
        # 检查学生在同一时间段是否有其他课程
        conflicting_schedules = (
            db.query(CourseScheduleModel, CourseModel)
            .join(CourseModel)
            .filter(
                CourseScheduleModel.course_id.in_(enrolled_course_ids),
                CourseScheduleModel.weekday == slot.weekday,
                CourseScheduleModel.start_time < slot.end_time,
                CourseScheduleModel.end_time > slot.start_time,
            )
            .all()
        )

        for conflict_schedule, conflict_course in conflicting_schedules:
            conflicts.append(
                {
                    "weekday": weekday_names[slot.weekday],
                    "conflict_course_name": conflict_course.name,
                    "conflict_time": f"{conflict_schedule.start_time.strftime('%H:%M')}-{conflict_schedule.end_time.strftime('%H:%M')}",
                    "new_time": f"{slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}",
                }
            )

    return conflicts


@router.post("/schedules")
async def create_course_schedule(
    schedule: CourseScheduleCreate, db: Session = Depends(get_db)
):
    # 验证课程是否存在
    course = db.query(CourseModel).filter(CourseModel.id == schedule.course_id).first()
    if not course:
        return response_error(code=404, message="课程不存在")

    # 检查课程是否已有时间安排
    existing_schedules = (
        db.query(CourseScheduleModel)
        .filter(CourseScheduleModel.course_id == schedule.course_id)
        .first()
    )

    if existing_schedules:
        return response_error(
            message="该课程已有时间安排，请先删除现有安排后再创建新的时间安排"
        )

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
                end_time=slot.end_time,
            )
            db.add(schedule_model)

        db.commit()

        response_data = {
            "time_slots": [
                {
                    "weekday": slot.weekday,
                    "start_time": slot.start_time.strftime("%H:%M"),
                    "end_time": slot.end_time.strftime("%H:%M"),
                }
                for slot in schedule.time_slots
            ]
        }

        return response_success(message="课程时间安排创建成功", data=response_data)
    except Exception as e:
        db.rollback()
        return response_error(message=f"创建课程时间安排失败: {str(e)}")


@router.get("/schedules/my")
async def get_my_schedules(
    db: Session = Depends(get_db), current_user=Security(get_current_user)
):
    # 获取学生选修的所有课程
    enrolled_courses = (
        db.query(StudentCourseModel, CourseModel)
        .join(CourseModel)
        .filter(StudentCourseModel.student_id == current_user.id)
        .all()
    )

    course_ids = [course.id for enrollment, course in enrolled_courses]

    # 修改查询，正确连接课程和教室
    schedules = (
        db.query(CourseScheduleModel, CourseModel, ClassroomModel)
        .join(CourseModel, CourseScheduleModel.course_id == CourseModel.id)
        .outerjoin(ClassroomModel, CourseModel.classroom_id == ClassroomModel.id)
        .filter(CourseScheduleModel.course_id.in_(course_ids))
        .all()
    )

    schedule_data = [
        {
            "course_id": course.id,
            "course_name": course.name,
            "start_date": course.start_date.strftime("%Y-%m-%d"),
            "end_date": course.end_date.strftime("%Y-%m-%d"),
            "weekday": schedule.weekday,
            "start_time": schedule.start_time.strftime("%H:%M"),
            "end_time": schedule.end_time.strftime("%H:%M"),
            "classroom_name": classroom.name if classroom else None,
        }
        for schedule, course, classroom in schedules
    ]

    return response_success(data=schedule_data)
