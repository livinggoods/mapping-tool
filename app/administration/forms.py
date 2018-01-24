from flask_wtf import Form
from flask_wtf.file import FileField, FileRequired
from wtforms import (StringField, TextAreaField, BooleanField, SelectField, SubmitField, ValidationError)
from wtforms.validators import DataRequired, Length, Email, Regexp
from ..models import Role, User, Geo, UserType, Branch

class UploadLocationForm(Form):
  file_field = FileField("Upload Excel Doc?", validators=[FileRequired()])
  submit = SubmitField('Submit')
  
  def __init__(self, *args, **kwargs):
    super(UploadLocationForm, self).__init__(*args, **kwargs)
