from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class Gender(int, Enum):
    MALE = 1
    FEMALE = 0

class Semester(int, Enum):
    FIRST = 1
    SECOND = 2

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
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class SemesterEnum(str, Enum):
    FIRST = "1"
    SECOND = "2"

class CourseCreate(CourseBase):
    academic_year: Optional[int] = None
    semester: Optional[Semester] = None

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[date]:
        if v is None:
            return None
        try:
            if isinstance(v, str):
                return datetime.strptime(v, '%Y-%m-%d').date()
            return v
        except ValueError:
            raise ValueError('日期格式必须为 YYYY-MM-DD')

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v: Optional[date], info) -> Optional[date]:
        if v is not None and 'start_date' in info.data:
            start_date = info.data['start_date']
            if isinstance(start_date, date) and v < start_date:
                raise ValueError('结束日期不能早于开始日期')
        return v

    @field_validator('academic_year')
    @classmethod
    def validate_academic_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1900:
            raise ValueError('学年必须大于1900')
        return v

class CourseUpdate(CourseBase):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    teacher: Optional[str] = None
    credits: Optional[int] = None
    max_student_num: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    academic_year: Optional[int] = None
    semester: Optional[Semester] = None

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[date]:
        if v is None:
            return None
        try:
            if isinstance(v, str):
                return datetime.strptime(v, '%Y-%m-%d').date()
            return v
        except ValueError:
            raise ValueError('日期格式必须为 YYYY-MM-DD')

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v: Optional[date], info) -> Optional[date]:
        if v is not None and 'start_date' in info.data:
            start_date = info.data['start_date']
            if isinstance(start_date, date) and v < start_date:
                raise ValueError('结束日期不能早于开始日期')
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