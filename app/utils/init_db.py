import hashlib

import mysql.connector
from mysql.connector import Error
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()


def get_password_md5(password: str) -> str:
    """使用MD5加密密码"""
    return hashlib.md5(password.encode()).hexdigest()


def create_database_if_not_exists():
    try:
        conn = mysql.connector.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            port=settings.DB_PORT,
        )

        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME}")
            cursor.close()
            conn.close()

    except Error as e:
        raise Exception(f"数据库初始化错误: {str(e)}")


# 确保数据库存在（可选，如果连接失败则跳过）
try:
    create_database_if_not_exists()
except Exception as e:
    print(f"警告: 数据库初始化失败，将在运行时重试: {str(e)}")

# 构建MySQL连接URL，使用mysql-connector-python驱动
SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_database():
    # 导入 models 以确保所有模型都被注册
    Base.metadata.create_all(bind=engine)
    insert_admin_account()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def insert_admin_account():
    from app.models import StudentModel  # 在函数内部导入

    db = SessionLocal()
    try:
        admin = db.query(StudentModel).filter(StudentModel.username == "admin").first()
        if not admin:
            default_admin = StudentModel(
                username="admin", password=get_password_md5("admin123"), is_active=True
            )
            db.add(default_admin)
            db.commit()
            print("已创建默认管理员账号")
    except Exception as e:
        db.rollback()
        print(f"创建管理员账号失败: {str(e)}")
    finally:
        db.close()
