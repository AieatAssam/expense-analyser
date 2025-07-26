"""Add analytics performance indexes

Revision ID: e1cd353514cc
Revises: 7f6f145a6a44
Create Date: 2025-07-26 10:27:51.938352

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1cd353514cc'
down_revision: Union[str, None] = '7f6f145a6a44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Analytics performance indexes ###
    
    # Composite index for analytics queries on receipts by user and date
    op.create_index(
        'ix_receipt_user_date_amount', 
        'receipt', 
        ['user_id', 'receipt_date', 'total_amount']
    )
    
    # Index for receipt date range queries
    op.create_index(
        'ix_receipt_date_range', 
        'receipt', 
        ['receipt_date']
    )
    
    # Index for line items with receipt and category for category breakdown
    op.create_index(
        'ix_line_item_receipt_category', 
        'line_item', 
        ['receipt_id', 'category_id', 'total_price']
    )
    
    # Index for category hierarchy queries
    op.create_index(
        'ix_category_parent_name', 
        'category', 
        ['parent_id', 'name']
    )
    
    # Index for receipt processing status and verification queries
    op.create_index(
        'ix_receipt_status_verified', 
        'receipt', 
        ['processing_status', 'is_verified']
    )
    
    # Index for full-text search on store names
    op.create_index(
        'ix_receipt_store_name_search', 
        'receipt', 
        ['store_name']
    )
    
    # Index for receipt number searches
    op.create_index(
        'ix_receipt_number_search', 
        'receipt', 
        ['receipt_number']
    )


def downgrade() -> None:
    # ### Drop analytics performance indexes ###
    
    op.drop_index('ix_receipt_number_search', table_name='receipt')
    op.drop_index('ix_receipt_store_name_search', table_name='receipt')
    op.drop_index('ix_receipt_status_verified', table_name='receipt')
    op.drop_index('ix_category_parent_name', table_name='category')
    op.drop_index('ix_line_item_receipt_category', table_name='line_item')
    op.drop_index('ix_receipt_date_range', table_name='receipt')
    op.drop_index('ix_receipt_user_date_amount', table_name='receipt')
