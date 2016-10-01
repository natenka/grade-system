"""Add email and labs

Revision ID: 012bbfd43836
Revises: 1851ef8a8083
Create Date: 2016-10-01 19:25:53.760118

"""

# revision identifiers, used by Alembic.
revision = '012bbfd43836'
down_revision = '1851ef8a8083'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('labs_to_check', sa.String(length=128), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'labs_to_check')
    ### end Alembic commands ###
