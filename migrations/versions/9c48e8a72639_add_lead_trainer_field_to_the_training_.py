"""Add lead_trainer field to the training_class

Revision ID: 9c48e8a72639
Revises: 0fbe8d283dee
Create Date: 2018-03-05 15:34:20.575368

"""

# revision identifiers, used by Alembic.
revision = '9c48e8a72639'
down_revision = '0fbe8d283dee'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('mapping', 'added_by',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.create_index(op.f('ix_training_training_status_id'), 'training', ['training_status_id'], unique=False)
    op.drop_index('ix_training_status', table_name='training')
    op.add_column('training_classes', sa.Column('lead_trainer', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'training_classes', 'users', ['lead_trainer'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'training_classes', type_='foreignkey')
    op.drop_column('training_classes', 'lead_trainer')
    op.create_index('ix_training_status', 'training', ['training_status_id'], unique=False)
    op.drop_index(op.f('ix_training_training_status_id'), table_name='training')
    op.alter_column('mapping', 'added_by',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###
