from ..database import SessionLocal
from ..models import models
import hashlib
from ..utils.logger import system_logger

def init_database():
    """初始化数据库，包括创建管理员用户等初始化操作"""
    init_admin()

def get_md5_password(password: str) -> str:
    """使用MD5加密密码"""
    return hashlib.md5(password.encode()).hexdigest()

def init_admin():
    """初始化管理员用户"""
    try:
        db = SessionLocal()
        # 检查是否已存在管理员用户
        admin_user = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin_user:
            # 创建管理员用户
            admin_user = models.User(
                username="admin",
                password=get_md5_password("admin123"),  # 使用MD5加密密码
                role="admin",
                is_active=True,
                email="admin@example.com"
            )
            db.add(admin_user)
            db.commit()
            system_logger.info("管理员用户初始化成功")
        db.close()
    except Exception as e:
        system_logger.error(f"初始化管理员用户失败: {str(e)}")
        raise e