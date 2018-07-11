"""Added error log model

Revision ID: bfcd024a1982
Revises: 61dc7d07bf3c
Create Date: 2018-07-11 14:34:38.735159

"""

# revision identifiers, used by Alembic.
revision = 'bfcd024a1982'
down_revision = '61dc7d07bf3c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('error_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('error', sa.String(length=1024), nullable=False),
    sa.Column('endpoint', sa.String(length=1024), nullable=False),
    sa.Column('payload', sa.Text(), nullable=True),
    sa.Column('datetime', sa.DateTime(), nullable=False),
    sa.Column('user', sa.Integer(), nullable=True),
    sa.Column('resolved', sa.Boolean(), nullable=False),
    sa.Column('http_method', sa.String(length=16), nullable=False),
    sa.Column('http_headers', sa.Text(), nullable=True),
    sa.Column('http_response_status_code', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user'], [u'users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('error_logs')
    # ### end Alembic commands ###
