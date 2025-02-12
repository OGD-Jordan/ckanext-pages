"""Page publish date nullable

Revision ID: 7fb527f56adf
Revises: a76b4a27e1cf
Create Date: 2025-02-12 13:57:17.011881

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7fb527f56adf'
down_revision = 'a76b4a27e1cf'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("ckanext_pages", "publish_date", existing_type=sa.DateTime, nullable=True)


def downgrade():
    op.alter_column("ckanext_pages", "publish_date", existing_type=sa.DateTime, nullable=False)
