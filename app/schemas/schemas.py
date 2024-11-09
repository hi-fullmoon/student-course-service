from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class CourseScheduleBase(BaseModel):
    course_id: int
    classroom_id: int
    day_of_week: int
    start_time: str
    end_time: str
    week_type: str

class CourseScheduleCreate(CourseScheduleBase):
    pass

class CourseSchedule(CourseScheduleBase):
    id: int

    class Config:
        from_attributes = True

class CourseBase(BaseModel):
    course_code: str
    name: str
    credit: float
    max_students: int
    teacher_id: int

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: int
    current_students: int
    schedules: List[CourseSchedule] = []

    class Config:
        from_attributes = True

class StudentBase(BaseModel):
    student_id: str
    name: str
    class_name: str

class StudentCreate(StudentBase):
    pass

class Student(StudentBase):
    id: int

    class Config:
        from_attributes = True

class EnrollmentBase(BaseModel):
    student_id: int
    course_id: int

class EnrollmentCreate(EnrollmentBase):
    pass

class Enrollment(EnrollmentBase):
    id: int
    grade: Optional[float] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: str
    role: str

class UserCreate(UserBase):
    password: str
    student_id: Optional[int] = None

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class BatchEnrollment(BaseModel):
    student_ids: List[int]
    course_id: int

class BatchGradeUpdate(BaseModel):
    enrollment_grades: List[dict]

class TeacherBase(BaseModel):
    teacher_id: str
    name: str
    department: str
    title: str

class TeacherCreate(TeacherBase):
    pass

class Teacher(TeacherBase):
    id: int

    class Config:
        from_attributes = True

class ClassroomBase(BaseModel):
    room_number: str
    building: str
    capacity: int
    has_projector: bool = False
    has_computer: bool = False

class ClassroomCreate(ClassroomBase):
    pass

class Classroom(ClassroomBase):
    id: int

    class Config:
        from_attributes = True

class CourseReviewBase(BaseModel):
    content: str
    rating: int
    is_anonymous: bool = False

class CourseReviewCreate(CourseReviewBase):
    enrollment_id: int

class CourseReview(CourseReviewBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationBase(BaseModel):
    title: str
    content: str
    type: str

class NotificationCreate(NotificationBase):
    user_id: int

class Notification(NotificationBase):
    id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    role: str
    student_id: Optional[str] = None

class TokenWithUserInfo(Token):
    user: UserInfo