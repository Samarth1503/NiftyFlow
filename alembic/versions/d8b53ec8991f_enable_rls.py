"""enable_rls

Revision ID: d8b53ec8991f
Revises: df092ecc32ef
Create Date: 2026-08-17 20:56:06.618013

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8b53ec8991f'
down_revision: Union[str, None] = 'df092ecc32ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Portfolios
    op.execute("ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;")
    op.execute("CREATE POLICY portfolios_user_policy ON portfolios FOR ALL USING (user_id = current_setting('app.current_user_id', true)::integer);")
    
    # Holdings
    op.execute("ALTER TABLE holdings ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY holdings_user_policy ON holdings FOR ALL 
        USING (portfolio_id IN (SELECT id FROM portfolios WHERE user_id = current_setting('app.current_user_id', true)::integer))
    """)
    
    # Transactions
    op.execute("ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY transactions_user_policy ON transactions FOR ALL 
        USING (portfolio_id IN (SELECT id FROM portfolios WHERE user_id = current_setting('app.current_user_id', true)::integer))
    """)
    
    # Watchlists
    op.execute("ALTER TABLE watchlists ENABLE ROW LEVEL SECURITY;")
    op.execute("CREATE POLICY watchlists_user_policy ON watchlists FOR ALL USING (user_id = current_setting('app.current_user_id', true)::integer);")

def downgrade() -> None:
    op.execute("DROP POLICY watchlists_user_policy ON watchlists;")
    op.execute("ALTER TABLE watchlists DISABLE ROW LEVEL SECURITY;")
    
    op.execute("DROP POLICY transactions_user_policy ON transactions;")
    op.execute("ALTER TABLE transactions DISABLE ROW LEVEL SECURITY;")
    
    op.execute("DROP POLICY holdings_user_policy ON holdings;")
    op.execute("ALTER TABLE holdings DISABLE ROW LEVEL SECURITY;")
    
    op.execute("DROP POLICY portfolios_user_policy ON portfolios;")
    op.execute("ALTER TABLE portfolios DISABLE ROW LEVEL SECURITY;")
