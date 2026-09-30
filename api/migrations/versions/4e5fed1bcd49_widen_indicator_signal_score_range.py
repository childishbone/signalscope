"""widen indicator signal score range

Revision ID: 4e5fed1bcd49
Revises: 87af3ef19695
Create Date: 2026-09-30 22:39:42.644229

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e5fed1bcd49'
down_revision: Union[str, Sequence[str], None] = '87af3ef19695'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # DMA, RSI, and Ichimoku each combine four independent +/-1 rules, so
    # their raw score can reach +/-4, not +/-2 as originally assumed.
    op.drop_constraint(op.f("ck_indicator_signals_score_range"), "indicator_signals", type_="check")
    op.create_check_constraint(
        op.f("ck_indicator_signals_score_range"), "indicator_signals", "score between -4 and 4"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f("ck_indicator_signals_score_range"), "indicator_signals", type_="check")
    op.create_check_constraint(
        op.f("ck_indicator_signals_score_range"), "indicator_signals", "score between -2 and 2"
    )