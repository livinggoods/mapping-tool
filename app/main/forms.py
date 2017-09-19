from flask_wtf import Form
from wtforms import StringField, TextAreaField, BooleanField, SelectField, \
    SubmitField, ValidationError, PasswordField, IntegerField, FloatField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from ..models import Role, User, Geo, UserType, Ward, County, Location, SubCounty, Parish, TrainingVenues,\
    Recruitments, TrainingStatus
from ..utils.utils import RequiredIf


class EditProfileForm(Form):
    name = StringField('Real name', validators=[Length(0, 64)])
    # location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    geo = SelectField('Geo', coerce=int)  # 'coerce': store values as ints
    user_type = SelectField('User Type', coerce=int)
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        # set the choices for the role dropdown list
        # give as a list of tuples, with each tuple consisting of two values:
        # and identifier of the item and the text to show in the control
        self.geo.choices = [(geo.id, geo.geo_name)
                             for geo in Geo.query.order_by(Geo.geo_name).all()]
        # self.geo.choices.insert(0, (-1, ''))

        self.user_type.choices = \
            [(utype.id, utype.name)
             for utype in UserType.query.order_by(UserType.name).all()]
        self.user_type.choices.insert(0, (-1, ''))


class EditProfileAdminForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    #username = StringField('Username', validators=[
    #    DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
    #                                      'Usernames must have only letters, '
    #                                      'numbers, dots or underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)  # 'coerce': store values as ints
    name = StringField('Real name', validators=[Length(0, 64)])
    # location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    geo = SelectField('Geo', coerce=int, validators=[DataRequired()])  # 'coerce': store values as ints
    user_type = SelectField('User Type', coerce=int)
    edit_password = BooleanField('Edit Password')
    password = PasswordField('Password', validators=[
        RequiredIf(edit_password=True), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[
        RequiredIf(password!=''), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        # set the choices for the role dropdown list
        # give as a list of tuples, with each tuple consisting of two values:
        # and identifier of the item and the text to show in the control
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]

        self.geo.choices = [(geo.id, geo.geo_name)
                             for geo in Geo.query.order_by(Geo.geo_name).all()]
        # self.geo.choices.insert(0, (-1, ''))

        self.user_type.choices = \
            [(utype.id, utype.name)
             for utype in UserType.query.order_by(UserType.name).all()]
        self.user_type.choices.insert(0, (-1, ''))

        self.user = user

    def validate_email(self, field):
        """
        Check if a change was made and ensure the new email does not already
        exist.
        """
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        """
        Check if a change was made and ensure the new username does not already
        exist.
        """
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class PostForm(Form):
    body = TextAreaField("What's on your mind?", validators=[DataRequired()])
    submit = SubmitField('Submit')
    
    
class IccmComponentForm(Form):
    component_name = StringField('Component Name', validators=[DataRequired(),
                                                               Length(1, 64, 'Maximun allowed characters is 64')])
    comment = TextAreaField("Comments")
    submit = SubmitField('Submit')


class TrainingForm(Form):
    """
    These are the fields that should be filled by the user about the new training
    """

    # id = StringField('id', validators=[DataRequired()])
    training_name = StringField('training_name', validators=[DataRequired()])
    country = SelectField('country', validators=[DataRequired()], coerce=int)
    county = SelectField('county', validators=[DataRequired()], coerce=int)
    location = SelectField('location', validators=[DataRequired()], coerce=int)
    subcounty = SelectField('subcounty', validators=[DataRequired()])
    ward = SelectField('ward', validators=[DataRequired()])
    district = StringField('district', validators=[DataRequired()])
    recruitment = SelectField('recruitment', validators=[DataRequired()])
    parish = SelectField('parish', validators=[DataRequired()], coerce=str)
    lat = FloatField('lat', validators=[DataRequired()])
    lon = FloatField('lon', validators=[DataRequired()])
    training_venue = SelectField('training_venue', validators=[DataRequired()])
    training_status = SelectField('training_status', validators=[DataRequired()], coerce=int)
    # client_time = StringField('client_time', validators=[DataRequired()])
    # created_by = StringField('created_by', validators=[DataRequired()])
    # date_created = StringField('date_created', validators=[DataRequired()])
    archived = SelectField('archived', validators=[DataRequired()], choices=[('0', 'False'), ('1', 'True')])
    comment = TextAreaField('comment', validators=[DataRequired()])
    date_commenced = IntegerField('Date Commenced', validators=[DataRequired()])
    date_completed = IntegerField('Date Completed', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(TrainingForm, self).__init__(*args, **kwargs)
        self.country.choices = [(geo.id, geo.geo_name)
                                for geo in Geo.query.order_by(Geo.geo_name).all()]
        self.county.choices = [(county.id, county.name)
                               for county in County.query.order_by(County.name).all()]
        self.location.choices = [(location.id, location.name)
                                 for location in Location.query.order_by(Location.name).all()]
        self.subcounty.choices = [(subcounty.id, subcounty.name)
                                  for subcounty in SubCounty.query.order_by(SubCounty.name).all()]
        self.ward.choices = [(ward.id, ward.name)
                             for ward in Ward.query.order_by(Ward.name).all()]
        self.recruitment.choices = [(recruitment.id, recruitment.name)
                                    for recruitment in Recruitments.query.order_by(Recruitments.name).all()]
        self.parish.choices = [(parish.id, parish.name)
                               for parish in Parish.query.order_by(Parish.name).all()]
        self.training_venue.choices = [(venue.id, venue.name)
                                       for venue in TrainingVenues.query.order_by(TrainingVenues.name).all()]
        self.training_status.choices = [(status.id, status.name)
                                        for status in TrainingStatus.query.order_by(TrainingStatus.name).all()]


class DeleteTrainingForm(Form):
    submit = SubmitField('Delete')


class TrainingClassForm(Form):
    class_name = StringField('Class name', validators=[DataRequired()])
    country = SelectField('Country', validators=[DataRequired()])
    archived = SelectField('Archived', validators=[DataRequired()], choices=[('0', 'False'), ('1', 'True')])

    def __init__(self, *args, **kwargs):
        super(TrainingClassForm, self).__init__(*args, **kwargs)
        self.country.choices = [(geo.id, geo.geo_name)
                                for geo in Geo.query.order_by(Geo.geo_name).all()]
