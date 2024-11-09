from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime
from sqlalchemy.sql import func

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(20), unique=True, index=True)
    name = Column(String(50))
    class_name = Column(String(50))
    enrollments = relationship("Enrollment", back_populates="student")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String(20), unique=True, index=True)
    name = Column(String(100))
    credit = Column(Float)
    max_students = Column(Integer)
    current_students = Column(Integer, default=0)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    teacher_info = relationship("Teacher", back_populates="courses")
    enrollments = relationship("Enrollment", back_populates="course")
    schedules = relationship("CourseSchedule", back_populates="course")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    grade = Column(Float, nullable=True)
    review = relationship("CourseReview", back_populates="enrollment", uselist=False)

    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    is_active = Column(Boolean, default=True)
    role = Column(String(20))
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    notifications = relationship("Notification", back_populates="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(String(20), unique=True, index=True)
    name = Column(String(50))
    department = Column(String(100))
    title = Column(String(50))
    courses = relationship("Course", back_populates="teacher_info")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String(20), unique=True, index=True)
    building = Column(String(50))
    capacity = Column(Integer)
    has_projector = Column(Boolean, default=False)
    has_computer = Column(Boolean, default=False)
    course_schedules = relationship("CourseSchedule", back_populates="classroom")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class CourseSchedule(Base):
    __tablename__ = "course_schedules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    classroom_id = Column(Integer, ForeignKey("classrooms.id"))
    day_of_week = Column(Integer)
    start_time = Column(String(5))
    end_time = Column(String(5))
    week_type = Column(String(4))
    course = relationship("Course", back_populates="schedules")
    classroom = relationship("Classroom", back_populates="course_schedules")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class CourseReview(Base):
    __tablename__ = "course_reviews"

    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), unique=True)
    content = Column(String(1000))
    rating = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_anonymous = Column(Boolean, default=False)
    enrollment = relationship("Enrollment", back_populates="review")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(200))
    content = Column(String(1000))
    type = Column(String(20))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user = relationship("User", back_populates="notifications")