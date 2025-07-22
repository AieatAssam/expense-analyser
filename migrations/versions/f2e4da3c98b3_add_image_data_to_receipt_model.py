"""Add image_data and image_format to Receipt model

Revision ID: f2e4da3c98b3
Revises: f2e4da3c98b2
Create Date: 2025-07-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2e4da3c98b3'
down_revision = 'f2e4da3c98b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add image_data and image_format columns
    op.add_column('receipt', sa.Column('image_data', sa.LargeBinary(), nullable=True))
    op.add_column('receipt', sa.Column('image_format', sa.String(length=10), nullable=True))
    
    # Mark image_path as nullable since we're transitioning to image_data
    op.alter_column('receipt', 'image_path', existing_type=sa.VARCHAR(length=255), nullable=True)


def downgrade() -> None:
    # Drop the new columns
    op.drop_column('receipt', 'image_format')
    op.drop_column('receipt', 'image_data')
    
    # Mark image_path as non-nullable again
    op.alter_column('receipt', 'image_path', existing_type=sa.VARCHAR(length=255), nullable=False)
