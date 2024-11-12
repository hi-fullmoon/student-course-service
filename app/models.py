import datetime
import hashlib
from datetime import timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Time,
)
from sqlalchemy.orm import Session, relationship

from app.schemas import Gender, Semester
from app.utils.init_db import Base


def get_default_password():
    """返回默认密码123456的MD5值"""
    return hashlib.md5("123456".encode()).hexdigest()


class StudentModel(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_number = Column(String(20), unique=True, index=True, comment="学号")
    username = Column(String(50), unique=True, index=True)
    password = Column(String(32), default=get_default_password())
    email = Column(String(100), unique=True, index=True)
    gender = Column(Enum(Gender), nullable=True)
    is_active = Column(Boolean, default=True)
    enrollment_date = Column(DateTime(timezone=True), nullable=True, comment="入学时间")
    class_name = Column(String(50), nullable=True, comment="班级名称")
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(timezone.utc),
        onupdate=lambda: datetime.datetime.now(timezone.utc),
    )

    courses = relationship("StudentCourseModel", back_populates="student")

    @classmethod
    def generate_student_number(cls, db: Session) -> str:
        # 获取当前年份
        current_year = datetime.datetime.now().year

        # 查询当前年份最大的学号
        latest_student = (
            db.query(cls)
            .filter(cls.student_number.like(f"{current_year}%"))
            .order_by(cls.student_number.desc())
            .first()
        )

        if latest_student:
            # 如果存在，获取序号并加1
            sequence = int(latest_student.student_number[4:]) + 1
        else:
            # 如果不存在，从1开始
            sequence = 1

        # 格式化学号：年份 + 4位序号
        return f"{current_year}{sequence:04d}"


class CourseModel(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True)
    name = Column(String(100), index=True)
    description = Column(String(500), nullable=True)
    teacher = Column(String(100))
    credits = Column(Integer)
    max_student_num = Column(Integer)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(timezone.utc),
        onupdate=lambda: datetime.datetime.now(timezone.utc),
    )
    start_date = Column(DateTime(timezone=True), nullable=True, comment="课程开始日期")
    end_date = Column(DateTime(timezone=True), nullable=True, comment="课程结束日期")
    academic_year = Column(Integer, nullable=True, comment="学年")
    semester = Column(Enum(Semester), nullable=True, comment="学期")

    students = relationship("StudentCourseModel", back_populates="course")
    schedules = relationship("CourseScheduleModel", back_populates="course")
    classroom = relationship("ClassroomModel", back_populates="courses")


class StudentCourseModel(Base):
    __tablename__ = "student_courses"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    enrollment_date = Column(
        DateTime, default=lambda: datetime.datetime.now(timezone.utc)
    )

    student = relationship("StudentModel", back_populates="courses")
    course = relationship("CourseModel", back_populates="students")


class CourseScheduleModel(Base):
    __tablename__ = "course_schedules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    weekday = Column(Integer)  # 0-6 表示周一到周日
    start_time = Column(Time)
    end_time = Column(Time)

    course = relationship("CourseModel", back_populates="schedules")


class ClassroomModel(Base):
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), comment="教室名称")
    capacity = Column(Integer, comment="容纳人数")
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(timezone.utc),
        onupdate=lambda: datetime.datetime.now(timezone.utc),
    )

    courses = relationship("CourseModel", back_populates="classroom")
