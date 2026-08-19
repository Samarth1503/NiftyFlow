"""force_rls

Revision ID: 609541c74978
Revises: bcb63d1da4a1
Create Date: 2026-08-18 10:16:58.350808

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '609541c74978'
down_revision: Union[str, None] = 'bcb63d1da4a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure RLS applies even to table owners
    op.execute("ALTER TABLE portfolios FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE holdings FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE transactions FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE watchlists FORCE ROW LEVEL SECURITY;")


def downgrade() -> None:
    op.execute("ALTER TABLE portfolios NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE holdings NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE transactions NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE watchlists NO FORCE ROW LEVEL SECURITY;")
