"""RescanTasks

Revision ID: b9aebd0a8593
Revises: 571892d95516
Create Date: 2019-03-19 02:51:39.362368

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b9aebd0a8593"
down_revision = "571892d95516"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "rescan_task",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date_added", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("target", sa.String(length=128), nullable=False),
        sa.Column("dispatched", sa.Boolean(), nullable=True),
        sa.Column("date_dispatched", sa.DateTime(), nullable=True),
        sa.Column("complete", sa.Boolean(), nullable=True),
        sa.Column("date_completed", sa.DateTime(), nullable=True),
        sa.Column("scan_id", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_rescan_task_complete"), "rescan_task", ["complete"], unique=False
    )
    op.create_index(
        op.f("ix_rescan_task_date_added"), "rescan_task", ["date_added"], unique=False
    )
    op.create_index(
        op.f("ix_rescan_task_date_completed"),
        "rescan_task",
        ["date_completed"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rescan_task_date_dispatched"),
        "rescan_task",
        ["date_dispatched"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rescan_task_dispatched"), "rescan_task", ["dispatched"], unique=False
    )
    op.create_index(
        op.f("ix_rescan_task_target"), "rescan_task", ["target"], unique=False
    )
    op.create_index(
        op.f("ix_rescan_task_scan_id"), "rescan_task", ["scan_id"], unique=True
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_rescan_task_scan_id"), table_name="rescan_task")
    op.drop_index(op.f("ix_rescan_task_target"), table_name="rescan_task")
    op.drop_index(op.f("ix_rescan_task_dispatched"), table_name="rescan_task")
    op.drop_index(op.f("ix_rescan_task_date_dispatched"), table_name="rescan_task")
    op.drop_index(op.f("ix_rescan_task_date_completed"), table_name="rescan_task")
    op.drop_index(op.f("ix_rescan_task_date_added"), table_name="rescan_task")
    op.drop_index(op.f("ix_rescan_task_complete"), table_name="rescan_task")
    op.drop_table("rescan_task")
    # ### end Alembic commands ###
