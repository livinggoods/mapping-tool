from flask_wtf import Form
from flask_wtf.file import FileField, FileRequired
from wtforms import (StringField, TextAreaField, PasswordField,
                     BooleanField, SelectField, SubmitField, ValidationError)
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from ..models import Role, User, Geo, UserType, Branch, Location

class UploadLocationForm(Form):
  file_field = FileField("Upload Excel Doc?", validators=[FileRequired()])
  submit = SubmitField('Submit')
  
  def __init__(self, *args, **kwargs):
    super(UploadLocationForm, self).__init__(*args, **kwargs)


class LocationUgForm(Form):
  name = StringField('Location Name', validators=[DataRequired(), Length(1, 64)])
  parent = SelectField('Parent', coerce=int)
  submit = SubmitField('Submit')
  
  def __init__(self, *args, **kwargs):
    super(LocationUgForm, self).__init__(*args, **kwargs)
