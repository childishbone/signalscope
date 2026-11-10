"""add bollinger indicator

Revision ID: a3c1d9e5b7f2
Revises: 4e5fed1bcd49
Create Date: 2026-11-10 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a3c1d9e5b7f2'
down_revision: Union[str, Sequence[str], None] = '4e5fed1bcd49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Bollinger Bands replaces Elliott Wave in the live app. 'elliott' stays
    # in the allowed list so previously stored Elliott history remains valid.
    op.drop_constraint(op.f("ck_indicator_signals_indicator"), "indicator_signals", type_="check")
    op.create_check_constraint(
        op.f("ck_indicator_signals_indicator"),
        "indicator_signals",
        "indicator in ('dma', 'rsi', 'ichimoku', 'elliott', 'bollinger', 'overall')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM indicator_signals WHERE indicator = 'bollinger'")
    op.drop_constraint(op.f("ck_indicator_signals_indicator"), "indicator_signals", type_="check")
    op.create_check_constraint(
        op.f("ck_indicator_signals_indicator"),
        "indicator_signals",
        "indicator in ('dma', 'rsi', 'ichimoku', 'elliott', 'overall')",
    )