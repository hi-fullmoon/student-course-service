"""add student_id to users

Revision ID: 202403150001
Revises: 202403141234
Create Date: 2024-03-15 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '202403150001'
down_revision = '202403141234'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 添加 student_id 列到 users 表
    op.add_column('users', sa.Column('student_id', sa.Integer(), nullable=True))
    # 添加外键约束
    op.create_foreign_key(
        'fk_users_student_id_students',
        'users', 'students',
        ['student_id'], ['id']
    )

def downgrade() -> None:
    # 删除外键约束
    op.drop_constraint('fk_users_student_id_students', 'users', type_='foreignkey')
    # 删除 student_id 列
    op.drop_column('users', 'student_id')