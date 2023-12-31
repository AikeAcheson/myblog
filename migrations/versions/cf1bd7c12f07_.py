"""empty message

Revision ID: cf1bd7c12f07
Revises: 7cd087f466bf
Create Date: 2022-10-16 21:43:52.976536

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf1bd7c12f07'
down_revision = '7cd087f466bf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('notebooks', sa.Column('file', sa.String(length=128), nullable=True))
    op.drop_index('ix_notebooks_filename', table_name='notebooks')
    op.create_index(op.f('ix_notebooks_file'), 'notebooks', ['file'], unique=True)
    op.drop_column('notebooks', 'filename')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('notebooks', sa.Column('filename', sa.VARCHAR(length=128), nullable=True))
    op.drop_index(op.f('ix_notebooks_file'), table_name='notebooks')
    op.create_index('ix_notebooks_filename', 'notebooks', ['filename'], unique=False)
    op.drop_column('notebooks', 'file')
    # ### end Alembic commands ###
