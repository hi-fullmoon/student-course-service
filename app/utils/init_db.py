import pymysql
from ..config import get_settings

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

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    init_database()