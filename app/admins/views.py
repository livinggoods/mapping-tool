import flask_admin as admin
from flask_admin.contrib import sqla
from flask_admin.contrib.sqla import filters
from ..models import (User, TrainingStatus)

class TrainingStatusAdmin(sqla.ModelView):
  column_exclude_list = ['name']
  
  column_choices = {
    'name': [
      ('draft', 'Draft'),
      ('completed', 'Completed'),
    ],
    'readonly':[
      ('1', 'True'),
      ('0', 'False'),
    ],
    'country': [
      ('KE', 'Kenya'),
      ('UG', 'Uganda'),
    ]
  }

  def __init__(self, session):
    # Just call parent class with predefined model.
    super(TrainingStatusAdmin, self).__init__(TrainingStatus, session)
  
# column_sortable_list = ('title', ('user', 'user.username'), 'date')