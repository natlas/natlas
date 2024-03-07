"""empty message

Revision ID: 997bbd9a505a
Revises: aeb6c660a13a
Create Date: 2018-07-17 13:21:47.150960

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "997bbd9a505a"
down_revision = "aeb6c660a13a"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(
        op.f("ix_scope_item_blacklist"), "scope_item", ["blacklist"], unique=False
    )
    op.create_index(op.f("ix_scope_item_target"), "scope_item", ["target"], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_scope_item_target"), table_name="scope_item")
    op.drop_index(op.f("ix_scope_item_blacklist"), table_name="scope_item")
    # ### end Alembic commands ###
