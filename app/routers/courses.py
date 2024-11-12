from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from sqlalchemy.orm import Session

from app.models import (
    ClassroomModel,
    CourseModel,
    CourseScheduleModel,
    StudentCourseModel,
    StudentModel,
)
from app.schemas import CourseCreate, CourseUpdate, CourseWithSchedule
from app.utils.auth import get_current_user
from app.utils.init_db import get_db
from app.utils.response import model_to_dict, response_error, response_success

router = APIRouter()


@router.post("/courses")
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    try:
        course_data = course.model_dump()

        # 如果提供了教室ID，检查教室是否存在
        if course_data.get("classroom_id"):
            classroom = (
                db.query(ClassroomModel)
                .filter(ClassroomModel.id == course_data["classroom_id"])
                .first()
            )
            if not classroom:
                return response_error(message="指定的教室不存在")

        db_course = CourseModel(**course_data)
        db.add(db_course)
        db.commit()
        db.refresh(db_course)

        # 转换为字典并添加教室信息
        course_dict = model_to_dict(db_course)
        course_dict["classroom"] = (
            model_to_dict(db_course.classroom) if db_course.classroom else None
        )
        course_dict["schedules"] = []

        return response_success(data=course_dict)
    except ValueError as e:
        return response_error(message=f"日期格式错误: {str(e)}")
    except Exception as e:
        return response_error(message=f"创建课程失败: {str(e)}")


@router.get("/courses", response_model=List[CourseWithSchedule])
def get_courses(
    name: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(CourseModel)

    if name:
        query = query.filter(CourseModel.name.ilike(f"%{name}%"))

    courses = query.offset(skip).limit(limit).all()

    # 转换为字典并添加教室信息
    result = []
    for course in courses:
        course_dict = model_to_dict(course)
        course_dict["schedules"] = [
            model_to_dict(schedule) for schedule in course.schedules
        ]
        course_dict["classroom_name"] = course.classroom.name
        result.append(course_dict)

    return response_success(data=result)


@router.get("/courses/my-selection")
def get_my_course_selection(
    name: Optional[str] = Query(None, description="课程名称"),
    code: Optional[str] = Query(None, description="课程代码"),
    teacher: Optional[str] = Query(None, description="教师姓名"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    is_enrolled: Optional[int] = Query(None, description="选课状态：1-已选，0-未选"),
    db: Session = Depends(get_db),
    current_user: StudentModel = Security(get_current_user),
):
    try:
        # 获取当前用户的所有选课记录
        my_enrollments = (
            db.query(StudentCourseModel)
            .filter(StudentCourseModel.student_id == current_user.id)
            .all()
        )
        enrolled_course_ids = {enrollment.course_id for enrollment in my_enrollments}

        # 构建基础查询
        query = db.query(CourseModel)

        # 根据选课状态筛选
        if is_enrolled is not None:
            if is_enrolled == 1:
                query = query.filter(CourseModel.id.in_(enrolled_course_ids))
            elif is_enrolled == 0:
                query = query.filter(CourseModel.id.notin_(enrolled_course_ids))

        # 应用其他过滤条件
        if name:
            query = query.filter(CourseModel.name.like(f"%{name}%"))
        if code:
            query = query.filter(CourseModel.code.like(f"%{code}%"))
        if teacher:
            query = query.filter(CourseModel.teacher.like(f"%{teacher}%"))

        try:
            if start_date:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(CourseModel.start_date >= start)
            if end_date:
                end = datetime.strptime(end_date, "%Y-%m-%d")
                query = query.filter(CourseModel.end_date <= end)
        except ValueError:
            return response_error(message="日期格式错误，请使用 YYYY-MM-DD 格式")

        # 执行查询
        courses = query.all()

        # 构建响应数据
        course_list = []
        for course in courses:
            # 获取该课程的选课人数
            enrolled_count = (
                db.query(StudentCourseModel)
                .filter(StudentCourseModel.course_id == course.id)
                .count()
            )

            course_data = model_to_dict(course)
            course_data.update(
                {
                    "is_enrolled": course.id in enrolled_course_ids,  # 是否已选
                    "enrolled_count": enrolled_count,  # 已选人数
                    "remaining_slots": course.max_student_num
                    - enrolled_count,  # 剩余名额
                }
            )
            course_list.append(course_data)

        return response_success(data=course_list)
    except Exception as e:
        return response_error(message=f"获取课程选择情况失败: {str(e)}")


@router.get("/courses/{course_id}", response_model=CourseWithSchedule)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")

    # 转换为字典并添加教室信息
    course_dict = model_to_dict(course)
    course_dict["schedules"] = [
        model_to_dict(schedule) for schedule in course.schedules
    ]
    course_dict["classroom"] = (
        model_to_dict(course.classroom) if course.classroom else None
    )

    return response_success(data=course_dict)


@router.post("/courses/{course_id}/enroll")
def enroll_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: StudentModel = Security(get_current_user),
):
    # 检查课程是否存在
    course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
    if not course:
        return response_error(code=404, message="课程不存在")

    # 检查学生是否已经选择该课程
    existing_enrollment = (
        db.query(StudentCourseModel)
        .filter(
            StudentCourseModel.student_id == current_user.id,
            StudentCourseModel.course_id == course_id,
        )
        .first()
    )

    if existing_enrollment:
        return response_error(message="已经选择了该课程")

    # 检查课程是否已满
    current_students = (
        db.query(StudentCourseModel)
        .filter(StudentCourseModel.course_id == course_id)
        .count()
    )

    if current_students >= course.max_student_num:
        return response_error(message="课程已满")

    # 检查时间冲突
    course_schedules = (
        db.query(CourseScheduleModel)
        .filter(CourseScheduleModel.course_id == course_id)
        .all()
    )

    if course_schedules:
        # 获取学生已选课程的时间安排
        enrolled_courses = (
            db.query(StudentCourseModel)
            .filter(StudentCourseModel.student_id == current_user.id)
            .all()
        )
        enrolled_course_ids = [ec.course_id for ec in enrolled_courses]

        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        conflicts = []

        existing_schedules = (
            db.query(CourseScheduleModel, CourseModel)
            .join(CourseModel)
            .filter(CourseScheduleModel.course_id.in_(enrolled_course_ids))
            .all()
        )

        # 检查每个时间段是否有冲突
        for new_schedule in course_schedules:
            for existing_schedule, existing_course in existing_schedules:
                if (
                    new_schedule.weekday == existing_schedule.weekday
                    and new_schedule.start_time < existing_schedule.end_time
                    and new_schedule.end_time > existing_schedule.start_time
                ):
                    conflicts.append(
                        f"{weekday_names[new_schedule.weekday]} "
                        f"{new_schedule.start_time.strftime('%H:%M')}-{new_schedule.end_time.strftime('%H:%M')} "
                        f"与课程《{existing_course.name}》"
                        f"({existing_schedule.start_time.strftime('%H:%M')}-{existing_schedule.end_time.strftime('%H:%M')}) "
                        f"时间冲突"
                    )

        if conflicts:
            conflicts_str = "\n".join(conflicts)
            return response_error(message=conflicts_str)

    try:
        # 创建选课记录
        new_enrollment = StudentCourseModel(
            student_id=current_user.id, course_id=course_id
        )
        db.add(new_enrollment)
        db.commit()
        return response_success(message="选课成功")
    except Exception as e:
        db.rollback()
        return response_error(message=f"选课失败: {str(e)}")


@router.put("/courses/{course_id}")
def update_course(
    course_id: int, course_update: CourseUpdate, db: Session = Depends(get_db)
):
    db_course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
    if not db_course:
        return response_error(code=404, message="课程不存在")

    try:
        update_data = course_update.model_dump(exclude_unset=True)

        # 如果要更新教室，检查新教室是否存在
        if "classroom_id" in update_data:
            if update_data["classroom_id"] is not None:
                classroom = (
                    db.query(ClassroomModel)
                    .filter(ClassroomModel.id == update_data["classroom_id"])
                    .first()
                )
                if not classroom:
                    return response_error(message="指定的教室不存在")

        for key, value in update_data.items():
            setattr(db_course, key, value)

        db.commit()
        db.refresh(db_course)

        # 转换为字典并添加教室信息
        course_dict = model_to_dict(db_course)
        course_dict["classroom"] = (
            model_to_dict(db_course.classroom) if db_course.classroom else None
        )
        course_dict["schedules"] = [
            model_to_dict(schedule) for schedule in db_course.schedules
        ]

        return response_success(message="课程更新成功", data=course_dict)
    except ValueError as e:
        return response_error(message=f"数据格式错误: {str(e)}")
    except Exception as e:
        return response_error(message=f"更新课程失败: {str(e)}")


@router.delete("/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    try:
        # 检查课程是否存在
        course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
        if not course:
            return response_error(code=404, message="课程不存在")

        # 删除相关的选课记录
        db.query(StudentCourseModel).filter(
            StudentCourseModel.course_id == course_id
        ).delete()

        # 删除课程时间安排
        db.query(CourseScheduleModel).filter(
            CourseScheduleModel.course_id == course_id
        ).delete()

        # 删除课程
        db.query(CourseModel).filter(CourseModel.id == course_id).delete()

        db.commit()
        return response_success(message="课程删除成功")
    except Exception as e:
        db.rollback()
        return response_error(message=f"删除课程失败: {str(e)}")
