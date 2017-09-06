"""Add foreign keys to recruitments

Revision ID: 644a1cccf9e1
Revises: 483b042632bc
Create Date: 2017-09-06 12:37:09.714622

"""

# revision identifiers, used by Alembic.
revision = '644a1cccf9e1'
down_revision = '483b042632bc'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    
    op.add_column('recruitments', sa.Column('county_id', sa.Integer(), nullable=True))
    op.add_column('recruitments', sa.Column('location_id', sa.Integer(), nullable=True))
    op.add_column('recruitments', sa.Column('subcounty_id', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_recruitments_county_id'), 'recruitments', ['county_id'], unique=False)
    op.create_index(op.f('ix_recruitments_location_id'), 'recruitments', ['location_id'], unique=False)
    op.create_index(op.f('ix_recruitments_subcounty_id'), 'recruitments', ['subcounty_id'], unique=False)
    op.create_foreign_key(None, 'recruitments', 'location', ['location_id'], ['id'])
    op.create_foreign_key(None, 'recruitments', 'subcounty', ['subcounty_id'], ['id'])
    op.create_foreign_key(None, 'recruitments', 'ke_county', ['county_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    
    op.drop_constraint(None, 'recruitments', type_='foreignkey')
    op.drop_constraint(None, 'recruitments', type_='foreignkey')
    op.drop_constraint(None, 'recruitments', type_='foreignkey')
    op.drop_index(op.f('ix_recruitments_subcounty_id'), table_name='recruitments')
    op.drop_index(op.f('ix_recruitments_location_id'), table_name='recruitments')
    op.drop_index(op.f('ix_recruitments_county_id'), table_name='recruitments')
    
    # ### end Alembic commands ###
