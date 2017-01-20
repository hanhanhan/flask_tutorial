"""empty message

Revision ID: ebd6e4421d8e
Revises: 1f5255f69039
Create Date: 2017-01-16 10:00:17.240045

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ebd6e4421d8e'
down_revision = '1f5255f69039'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('about_me', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('location', sa.String(length=64), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'location')
    op.drop_column('users', 'about_me')
    # ### end Alembic commands ###
