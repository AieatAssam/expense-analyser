"""add_processing_events_table

Revision ID: f2e4da3c98b4
Revises: f2e4da3c98b3
Create Date: 2025-07-22 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision: str = 'f2e4da3c98b4'
down_revision: Union[str, None] = 'f2e4da3c98b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the processing_event table
    op.create_table(
        'processing_event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('receipt_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('message', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('details', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['receipt_id'], ['receipt.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on receipt_id
    op.create_index(op.f('ix_processing_event_receipt_id'), 'processing_event', ['receipt_id'], unique=False)
    # Create index on timestamp for faster lookups
    op.create_index(op.f('ix_processing_event_timestamp'), 'processing_event', ['timestamp'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_processing_event_timestamp'), table_name='processing_event')
    op.drop_index(op.f('ix_processing_event_receipt_id'), table_name='processing_event')
    
    # Drop table
    op.drop_table('processing_event')
