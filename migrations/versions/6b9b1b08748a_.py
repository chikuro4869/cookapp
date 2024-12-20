"""empty message

Revision ID: 6b9b1b08748a
Revises: 7f5a8a20850e
Create Date: 2024-12-02 20:34:30.867423

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6b9b1b08748a'
down_revision = '7f5a8a20850e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('dailymission')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('dailymission',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=True),
    sa.Column('date', sa.DATE(), nullable=False),
    sa.Column('breakfast', sa.BOOLEAN(), nullable=True),
    sa.Column('lunch', sa.BOOLEAN(), nullable=True),
    sa.Column('dinner', sa.BOOLEAN(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
