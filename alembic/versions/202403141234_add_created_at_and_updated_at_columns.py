"""Add created_at and updated_at columns

Revision ID: 202403141234
Revises:
Create Date: 2024-03-14 12:34:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '202403141234'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 为每个表添加 created_at 和 updated_at 列
    tables_without_timestamps = [
        'students', 'courses', 'enrollments', 'users', 'teachers',
        'classrooms', 'course_schedules'
    ]

    # 为没有时间戳的表添加两个列
    for table in tables_without_timestamps:
        op.add_column(table, sa.Column('created_at', sa.DateTime(timezone=True),
                     server_default=sa.text('CURRENT_TIMESTAMP')))
        op.add_column(table, sa.Column('updated_at', sa.DateTime(timezone=True),
                     nullable=True))

    # 为已有 created_at 的表只添加 updated_at
    tables_with_created_at = ['course_reviews', 'notifications']
    for table in tables_with_created_at:
        op.add_column(table, sa.Column('updated_at', sa.DateTime(timezone=True),
                     nullable=True))

def downgrade():
    # 删除添加的列
    tables_without_timestamps = [
        'students', 'courses', 'enrollments', 'users', 'teachers',
        'classrooms', 'course_schedules'
    ]

    for table in tables_without_timestamps:
        op.drop_column(table, 'updated_at')
        op.drop_column(table, 'created_at')

    # 只删除 updated_at
    tables_with_created_at = ['course_reviews', 'notifications']
    for table in tables_with_created_at:
        op.drop_column(table, 'updated_at')