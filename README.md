# 学生选课系统 (Student Course System)

## 功能特性

- 用户认证与授权
- 课程管理
- 学生选课
- 成绩管理
- 教室管理
- 课程评价
- 课程安排
- 通知系统
- 报表生成

## 技术栈

- FastAPI
- SQLAlchemy
- Alembic
- MySQL
- Pydantic
- Python-JWT

## 安装与运行

1. 克隆项目
   git clone [repository-url]
   cd student-course-service

2. 创建虚拟环境
   python -m venv venv
   source venv/bin/activate # Linux/macOS
   或
   .\venv\Scripts\activate # Windows

3. 安装依赖
   pip install -r requirements.txt

4. 配置环境变量
   cp .env.example .env
   编辑 .env 文件，设置必要的环境变量

5. 初始化数据库
   alembic upgrade head

6. 运行服务
   uvicorn app.main:app --reload

## API 文档

启动服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 数据库迁移

创建新的迁移：
alembic revision --autogenerate -m "描述信息"

应用迁移：
alembic upgrade head

## 环境变量配置

项目使用 .env 文件进行配置，主要包含以下配置项：

# 数据库配置

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=student_course_system

# JWT 配置

SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 系统配置

MAX_COURSES_PER_STUDENT=10
MIN_STUDENTS_PER_COURSE=5
COURSE_SELECTION_ENABLED=true
GRADE_INPUT_ENABLED=true

## 开发团队

// TODO:

## 许可证

// TODO:
