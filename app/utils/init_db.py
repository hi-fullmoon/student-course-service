import pymysql
from ..config import get_settings
from passlib.context import CryptContext
import logging

# 创建密码加密工具
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_database():
    settings = get_settings()

    # 连接MySQL服务器
    conn = pymysql.connect(
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        charset='utf8mb4'
    )
    cursor = conn.cursor()

    # 创建数据库
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME}")
    cursor.execute(f"USE {settings.DB_NAME}")

    # 设置字符集
    cursor.execute("ALTER DATABASE `{}` CHARACTER SET 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'".format(
        settings.DB_NAME
    ))

    # 创建用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            role VARCHAR(20) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    # 检查是否存在管理员账号
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'ADMIN'")
    admin_count = cursor.fetchone()[0]

    # 如果不存在管理员账号，创建一个默认管理员
    if admin_count == 0:
        default_admin = {
            'username': 'admin',
            'hashed_password': pwd_context.hash('admin123'),  # 默认密码
            'email': 'admin@example.com',
            'role': 'ADMIN',
            'is_active': 1
        }

        try:
            cursor.execute("""
                INSERT INTO users (username, hashed_password, email, role, is_active)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                default_admin['username'],
                default_admin['hashed_password'],
                default_admin['email'],
                default_admin['role'],
                default_admin['is_active']
            ))
            conn.commit()
            logging.info("Default admin account created successfully")
        except Exception as e:
            logging.error(f"Error creating admin account: {str(e)}")
            conn.rollback()

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    init_database()