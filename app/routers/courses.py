from fastapi import APIRouter, Depends, Query, Security
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models import CourseModel, StudentCourseModel, StudentModel
from app.schemas import CourseCreate, CourseUpdate
from app.utils.init_db import get_db
from app.utils.auth import oauth2_scheme, get_current_user
from app.utils.response import response_success, response_error, model_to_dict

router = APIRouter()

@router.post("/courses")
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    try:
        # CourseCreate 的验证器会自动将 start_time 转换为 datetime 对象
        course_data = course.model_dump()
        db_course = CourseModel(**course_data)
        db.add(db_course)
        db.commit()
        db.refresh(db_course)
        return response_success(data=model_to_dict(db_course))
    except ValueError as e:
        return response_error(message=f"日期格式错误: {str(e)}")
    except Exception as e:
        return response_error(message=f"创建课程失败: {str(e)}")

@router.get("/courses")
def get_courses(
    name: Optional[str] = Query(None, description="课程名称"),
    code: Optional[str] = Query(None, description="课程代码"),
    teacher: Optional[str] = Query(None, description="教师姓名"),
    start_time: Optional[str] = Query(None, description="开始时间 (YYYY-MM-DD)"),
    end_time: Optional[str] = Query(None, description="结束时间 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    query = db.query(CourseModel)

    if name:
        query = query.filter(CourseModel.name.like(f"%{name}%"))
    if code:
        query = query.filter(CourseModel.code.like(f"%{code}%"))
    if teacher:
        query = query.filter(CourseModel.teacher.like(f"%{teacher}%"))

    try:
        if start_time:
            start_date = datetime.strptime(start_time, "%Y-%m-%d")
            query = query.filter(CourseModel.start_time >= start_date)
        if end_time:
            end_date = datetime.strptime(end_time, "%Y-%m-%d")
            query = query.filter(CourseModel.end_time <= end_date)
    except ValueError:
        return response_error(message="日期格式错误，请使用 YYYY-MM-DD 格式")

    courses = query.all()
    return response_success(data=[model_to_dict(course) for course in courses])

@router.get("/courses/my-selection")
def get_my_course_selection(
    name: Optional[str] = Query(None, description="课程名称"),
    code: Optional[str] = Query(None, description="课程代码"),
    teacher: Optional[str] = Query(None, description="教师姓名"),
    start_time: Optional[str] = Query(None, description="开始时间 (YYYY-MM-DD)"),
    end_time: Optional[str] = Query(None, description="结束时间 (YYYY-MM-DD)"),
    is_enrolled: Optional[int] = Query(None, description="选课状态：1-已选，0-未选"),
    db: Session = Depends(get_db),
    current_user: StudentModel = Security(get_current_user)
):
    try:
        # 获取当前用户的所有选课记录
        my_enrollments = db.query(StudentCourseModel).filter(
            StudentCourseModel.student_id == current_user.id
        ).all()
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
            if start_time:
                start_date = datetime.strptime(start_time, "%Y-%m-%d")
                query = query.filter(CourseModel.start_time >= start_date)
            if end_time:
                end_date = datetime.strptime(end_time, "%Y-%m-%d")
                query = query.filter(CourseModel.end_time <= end_date)
        except ValueError:
            return response_error(message="日期格式错误，请使用 YYYY-MM-DD 格式")

        # 执行查询
        courses = query.all()

        # 构建响应数据
        course_list = []
        for course in courses:
            # 获取该课程的选课人数
            enrolled_count = db.query(StudentCourseModel).filter(
                StudentCourseModel.course_id == course.id
            ).count()

            course_data = model_to_dict(course)
            course_data.update({
                "is_enrolled": course.id in enrolled_course_ids,  # 是否已选
                "enrolled_count": enrolled_count,  # 已选人数
                "remaining_slots": course.max_student_num - enrolled_count  # 剩余名额
            })
            course_list.append(course_data)

        return response_success(data=course_list)
    except Exception as e:
        return response_error(message=f"获取课程选择情况失败: {str(e)}")

@router.get("/courses/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
    if not course:
        return response_error(code=404, message="课程不存在")
    return response_success(data=course)

@router.post("/courses/{course_id}/enroll")
def enroll_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: StudentModel = Security(get_current_user)
):
    # 检查课程是否存在
    course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
    if not course:
        return response_error(code=404, message="课程不存在")

    # 检查学生是否已经选择该课程
    existing_enrollment = db.query(StudentCourseModel).filter(
        StudentCourseModel.student_id == current_user.id,
        StudentCourseModel.course_id == course_id
    ).first()

    if existing_enrollment:
        return response_error(message="已经选择了该课程")

    # 检查课程是否已满
    current_students = db.query(StudentCourseModel).filter(
        StudentCourseModel.course_id == course_id
    ).count()

    if current_students >= course.max_student_num:
        return response_error(message="课程已满")

    try:
        # 创建选课记录
        new_enrollment = StudentCourseModel(
            student_id=current_user.id,
            course_id=course_id
        )
        db.add(new_enrollment)
        db.commit()
        return response_success(message="选课成功")
    except Exception as e:
        return response_error(message=f"选课失败: {str(e)}")

@router.put("/courses/{course_id}")
def update_course(
    course_id: int,
    course_update: CourseUpdate,
    db: Session = Depends(get_db)
):
    # 检查课程是否存在
    db_course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
    if not db_course:
        return response_error(code=404, message="课程不存在")

    try:
        # 获取更新数据，排除None值
        update_data = course_update.model_dump(exclude_unset=True)

        # 如果没有提供任何更新数据
        if not update_data:
            return response_error(message="没有提供任何更新数据")

        # 更新课程信息
        for key, value in update_data.items():
            setattr(db_course, key, value)

        db.commit()
        db.refresh(db_course)

        return response_success(
            message="课程更新成功",
            data=model_to_dict(db_course)
        )
    except ValueError as e:
        return response_error(message=f"数据格式错误: {str(e)}")
    except Exception as e:
        return response_error(message=f"更新课程失败: {str(e)}")