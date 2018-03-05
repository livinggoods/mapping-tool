from wtforms.validators import Optional, DataRequired
import re
import os
import csv

class RequiredIf(object):
  """Validates field conditionally.
  Usage::
      login_method = StringField('', [AnyOf(['email', 'facebook'])])
      email = StringField('', [RequiredIf(login_method='email')])
      password = StringField('', [RequiredIf(login_method='email')])
      facebook_token = StringField('', [RequiredIf(login_method='facebook')])
  """

  def __init__(self, *args, **kwargs):
    self.conditions = kwargs

  def __call__(self, form, field):
    for name, data in self.conditions.iteritems():
      if name not in form._fields:
        Optional(form, field)
      else:
        condition_field = form._fields.get(name)
        if condition_field.data == data and not field.data:
          DataRequired()(form, field)
    Optional()(form, field)


def validate_uuid(uuid_string):
  UUID_RE = re.compile(r'^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$', re.IGNORECASE)
  return bool(UUID_RE.search(str(uuid_string)))


def process_location_csv(path):
  csv_rows=[]
  with open(os.path.abspath(path)) as csvfile:
    #expects the csv to be single column
    reader = csv.DictReader(csvfile)
    title = reader.fieldnames
    for row in reader:
      csv_rows.extend([{title[i]:row[title[i]].title() for i in range(len(title))}])
    return csv_rows