"""process timeouts for web and vnc screenshots

Revision ID: 6147093c140b
Revises: d4685e98a91f
Create Date: 2019-10-17 20:50:25.905796

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6147093c140b"
down_revision = "d4685e98a91f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "agent_config", sa.Column("vncScreenshotTimeout", sa.Integer(), nullable=True)
    )
    op.add_column(
        "agent_config", sa.Column("webScreenshotTimeout", sa.Integer(), nullable=True)
    )

    newColumns = {"vncScreenshotTimeout": 60, "webScreenshotTimeout": 60}
    for col_name, col_def in newColumns.items():
        new_col = sa.table("agent_config", sa.Column(col_name))
        op.execute(new_col.update().values(**{col_name: col_def}))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("agent_config", "webScreenshotTimeout")
    op.drop_column("agent_config", "vncScreenshotTimeout")
    # ### end Alembic commands ###
