"""Merge invitation table with image data and processing events

Revision ID: 7f6f145a6a44
Revises: f2e4da3c98b4, 41b92049199b
Create Date: 2025-07-23 00:03:17.554599

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f6f145a6a44'
down_revision: Union[str, None] = ('f2e4da3c98b4', '41b92049199b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
