from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class Gender(int, Enum):
    MALE = 1
    FEMALE = 0

class ClassBase(BaseModel):
    name: str
    grade: int

class ClassCreate(ClassBase):
    pass

class ClassUpdate(ClassBase):
    name: str | None = None
    grade: int | None = None

class Class(ClassBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StudentBase(BaseModel):
    username: str
    student_number: str | None = None
    class_name: str | None = None
    gender: Gender | None = None
    email: EmailStr
    enrollment_date: datetime | None = None

class StudentCreate(StudentBase):
    pass

class StudentUpdate(StudentBase):
    student_number: str | None = None
    username: str | None = None
    gender: Gender | None = None
    email: EmailStr | None = None
    enrollment_date: datetime | None = None
    class_name: str | None = None

class Student(StudentBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CourseBase(BaseModel):
    code: str
    name: str
    description: str
    teacher: str
    credits: int
    max_student_num: int
    start_time: datetime | None = None
    end_time: datetime | None = None

class CourseCreate(CourseBase):
    start_time: str  # 接收 YYYY-MM-dd 格式的字符串
    end_time: str    # 接收 YYYY-MM-dd 格式的字符串

    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_date(cls, v: str) -> datetime:
        try:
            # 将字符串转换为 datetime 对象
            return datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('日期格式必须为 YYYY-MM-DD')

    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v: datetime, info) -> datetime:
        if 'start_time' in info.data:
            start_time = info.data['start_time']
            if isinstance(start_time, datetime) and v < start_time:
                raise ValueError('结束时间不能早于开始时间')
        return v

class CourseUpdate(CourseBase):
    start_time: str  # 接收 YYYY-MM-dd 格式的字符串
    end_time: str    # 接收 YYYY-MM-dd 格式的字符串

    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_date(cls, v: str) -> datetime:
        try:
            # 将字符串转换为 datetime 对象
            return datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('日期格式必须为 YYYY-MM-DD')

    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v: datetime, info) -> datetime:
        if 'start_time' in info.data:
            start_time = info.data['start_time']
            if isinstance(start_time, datetime) and v < start_time:
                raise ValueError('结束时间不能早于开始时间')
        return v

class Course(CourseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Schedule(BaseModel):
    id: int
    student_id: int
    course_id: int
    enrollment_date: datetime
    course: Course

    class Config:
        from_attributes = True

class LoginData(BaseModel):
    username: str
    password: str