"""empty message

Revision ID: 534629d595b0
Revises: 5813ecebaaea
Create Date: 2022-10-14 17:36:52.461569

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '534629d595b0'
down_revision = '5813ecebaaea'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('avatar_hash', sa.String(length=32), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'avatar_hash')
    # ### end Alembic commands ###