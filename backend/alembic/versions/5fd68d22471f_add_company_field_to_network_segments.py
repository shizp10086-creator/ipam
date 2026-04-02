"""add_company_field_to_network_segments

Revision ID: 5fd68d22471f
Revises: 001
Create Date: 2026-02-07 22:11:56.388735

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5fd68d22471f'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 company 字段到 network_segments 表
    op.add_column('network_segments', sa.Column('company', sa.String(length=100), nullable=True, comment='所属公司'))


def downgrade() -> None:
    # 删除 company 字段
    op.drop_column('network_segments', 'company')
