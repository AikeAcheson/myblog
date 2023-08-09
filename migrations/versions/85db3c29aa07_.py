"""empty message

Revision ID: 85db3c29aa07
Revises: d9aaa5b13e08
Create Date: 2022-10-26 15:24:59.255445

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '85db3c29aa07'
down_revision = 'd9aaa5b13e08'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('notebook_comments', 'body_html')
    op.drop_column('post_comments', 'body_html')
    op.drop_column('posts', 'body_html')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('posts', sa.Column('body_html', sa.TEXT(), nullable=True))
    op.add_column('post_comments', sa.Column('body_html', sa.TEXT(), nullable=True))
    op.add_column('notebook_comments', sa.Column('body_html', sa.TEXT(), nullable=True))
    # ### end Alembic commands ###