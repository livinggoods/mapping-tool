from flask_wtf import Form
from flask_wtf.file import FileAllowed
from wtforms import (StringField, TextAreaField, BooleanField, SelectField, DateField, HiddenField,
                     SubmitField, ValidationError, PasswordField, IntegerField, FloatField, FileField)
from wtforms.validators import DataRequired, Length, Email, EqualTo, InputRequired
from ..models import (Role, User, Geo, UserType, Ward, County, Location, SubCounty, Parish, TrainingVenues,
                      Recruitments, TrainingStatus, TrainingSessionType, SessionTopic, Trainees, Registration,
                      Mapping)
from ..utils.utils import RequiredIf
from wtforms.fields.html5 import DateField
from flask_login import current_user


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
    lat = FloatField('Latitude', validators=[InputRequired()])
    lon = FloatField('Longitude', validators=[InputRequired()])
    training_name = StringField('Training Name', validators=[DataRequired()])
    country = SelectField('Country', validators=[DataRequired()], coerce=int)
    county = SelectField('County', validators=[RequiredIf(country=1)], coerce=int)
    location = SelectField('Location', validators=[RequiredIf(country=2)], coerce=int)
    subcounty = SelectField('Sub County', validators=[RequiredIf(country=1)])
    ward = SelectField('Ward', validators=[RequiredIf(country=1)])
    district = StringField('District', validators=[RequiredIf(country=2)])
    recruitment = SelectField('Recruitment', coerce=str)
    parish = SelectField('Parish', validators=[RequiredIf(country=2)], coerce=str)
    training_venue = SelectField('Training Venue')
    training_status = SelectField('Training Status', coerce=int)
    comment = TextAreaField('Comment')
    date_commenced = DateField('Date Commenced', format='%Y-%m-%d')
    date_completed = DateField('Date Completed', format='%Y-%m-%d')
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(TrainingForm, self).__init__(*args, **kwargs)
        self.country.choices = [(geo.id, geo.geo_name)
                                for geo in Geo.query.order_by(Geo.geo_name).all()]

        self.county.choices = [(county.id, county.name.title())
                               for county in County.query.order_by(County.name).all()]
        self.location.choices = [(location.id, location.name.title())
                                 for location in
                                 Location.query.filter_by(country=current_user.location).order_by(Location.name).all()]
        self.subcounty.choices = [(subcounty.id, subcounty.name.title())
                                  for subcounty in SubCounty.query.filter_by(country=current_user.location).order_by(
                SubCounty.name).all()]
        self.ward.choices = [(ward.id, ward.name.title())
                             for ward in Ward.query.order_by(Ward.name).all()]
        self.recruitment.choices = [(recruitment.id, recruitment.name)
                                    for recruitment in Recruitments.query.order_by(Recruitments.name).all()]
        self.recruitment.choices.insert(0, ('', '---'))

        self.parish.choices = [(parish.id, parish.name)
                               for parish in Parish.query.order_by(Parish.name).all()]

        self.training_venue.choices = [(venue.id, venue.name)
                                       for venue in TrainingVenues.query.order_by(TrainingVenues.name).all()]
        self.training_venue.choices.insert(0, ('-1', 'None'))
        self.training_status.choices = [(status.id, status.name)
                                        for status in TrainingStatus.query.order_by(TrainingStatus.name).all()]
        self.training_status.choices.insert(0, (-1, 'None'))


class DeleteTrainingForm(Form):
    submit = SubmitField('Delete')


class TrainingClassForm(Form):
    class_name = StringField('Class name', validators=[DataRequired()])
    country = SelectField('Country', validators=[DataRequired()], coerce=int)
    archived = SelectField('Archived', validators=[DataRequired()], choices=[('0', 'False'), ('1', 'True')])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(TrainingClassForm, self).__init__(*args, **kwargs)
        self.country.choices = [(geo.id, geo.geo_name)
                                for geo in Geo.query.order_by(Geo.geo_name).all()]


class TrainingSessionForm(Form):
    training_session_type = SelectField('Session type', validators=[DataRequired()], coerce=int)
    trainer = SelectField('Trainer', validators=[DataRequired()], coerce=int)
    country = SelectField('Country', validators=[DataRequired()], coerce=int)
    archived = SelectField('Archived', validators=[DataRequired()], choices=[('0', 'False'), ('1', 'True')])
    comment = TextAreaField('Comment', validators=[DataRequired()])
    session_topic = SelectField('Session\'s topic', validators=[DataRequired()], coerce=int)
    session_lead_trainer = SelectField('Lead Trainer', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(TrainingSessionForm, self).__init__(*args, **kwargs)
        self.training_session_type.choices = [(session_type.id, session_type.session_name)
                                              for session_type in TrainingSessionType.query.
                                              order_by(TrainingSessionType.session_name).all()]
        self.trainer.choices = [(trainer.id, trainer.username)
                                for trainer in User.query.order_by(User.username).all()]
        self.country.choices = [(geo.id, geo.geo_name)
                                for geo in Geo.query.order_by(Geo.geo_name).all()]
        self.session_topic.choices = [(topic.id, topic.name)
                              for topic in SessionTopic.query.order_by(SessionTopic.name).all()]
        self.session_lead_trainer.choices = [(trainer.id, trainer.username)
                                             for trainer in User.query.order_by(User.username).all()]


class SessionTopicForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    country = SelectField('Country', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(SessionTopicForm, self).__init__(*args, **kwargs)
        self.country.choices = [(geo.geo_code, geo.geo_name)
                                for geo in Geo.query.order_by(Geo.geo_name).all()]


class SessionTypeForm(Form):
    session_name = StringField('Name', validators=[DataRequired()])
    country = SelectField('Country', validators=[DataRequired()], coerce=int)
    archived = SelectField('Archived', validators=[], choices=[('0', 'False'), ('1', 'True')])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(SessionTypeForm, self).__init__(*args, **kwargs)
        self.country.choices = [(geo.id, geo.geo_name)
                                for geo in Geo.query.order_by(Geo.geo_name).all()]


class SessionAttendanceForm(Form):
    trainee = BooleanField('', validators=[DataRequired()])
    training_session_type = SelectField('Session Type', validators=[DataRequired()])
    country = SelectField('', validators=[DataRequired()])
    archived = SelectField('', validators=[DataRequired()], choices=[('0', 'False'), ('1', 'True')])
    comment = TextAreaField('', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):

        super(SessionAttendanceForm, self).__init__(*args, **kwargs)
        self.country.choices = [(geo.id, geo.geo_name)
                                for geo in Geo.query.order_by(Geo.geo_name).all()]
        self.trainee.choices = [(trainee.id, trainee.id)
                                for trainee in Trainees.query.join(Trainees.registration_id)
                                    .order_by(Registration.name).all()]
        self.training_session_type.choices = [(session_type.id, session_type.name)
                                              for session_type in TrainingSessionType.
                                                  query.order_by(TrainingSessionType.session_name).all()]


class TrainingVenueForm(Form):
    lat = FloatField('Latitude', validators=[DataRequired()])
    lon = FloatField('Longitude', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    mapping = SelectField('Mapping', validators=[DataRequired()])
    inspected = SelectField('Inspected', validators=[DataRequired()], choices=[('0', 'False'), ('1', 'True')])
    country = SelectField('Country', validators=[DataRequired()], coerce=int)
    selected = SelectField('Selected', validators=[DataRequired()], choices=[('0', 'False'), ('1', 'True')])
    capacity = IntegerField('Capacity', validators=[DataRequired()])
    archived = SelectField('Archived', validators=[DataRequired()], choices=[('0', 'False'), ('1', 'True')])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(TrainingVenueForm, self).__init__(*args, **kwargs)
        self.mapping.choices = [(mapping.id, mapping.name)
                                for mapping in Mapping.query.order_by(Mapping.name).all()]
        self.country.choices = [(geo.id, geo.geo_name)
                                for geo in Geo.query.order_by(Geo.geo_name).all()]


class QuestionsCSVUploadForm(Form):
    csv_file = FileField('CSV File to Upload',
                         validators=[
                             DataRequired(),
                             FileAllowed(['csv', 'xls', 'xlsx'], 'Invalid file format')]
                         )
    submit = SubmitField('Submit')


class TrainingRoleForm(Form):
    id = HiddenField("ID")
    role_name = StringField("Role Name", validators=[DataRequired(), Length(3, 19)])
    readonly = SelectField('Allow Editing', validators=[DataRequired()], choices=[('0', 'Yes'), ('1', 'No')])
    country = SelectField('Country', validators=[DataRequired()], coerce=int)
    submit = SubmitField("Save")
    
    def __init__(self, *args, **kwargs):
        super(TrainingRoleForm, self).__init__(*args, **kwargs)
        self.country.choices = [(geo.id, geo.geo_name)
                                for geo in Geo.query.order_by(Geo.geo_name).all()]


class CertTypeForm(Form):
    """
    These are the fields that should be filled by the user about the new certification type
    """
    name = StringField('Name', validators=[InputRequired()])
    proportion= FloatField('Proportion', validators=[InputRequired()], default=0)
    archived = BooleanField('archived', default=False)
    country = SelectField('Country', validators=[DataRequired()], coerce=int)

    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(CertTypeForm, self).__init__(*args, **kwargs)
        self.country.choices = [(geo.id, geo.geo_name)
                                for geo in Geo.query.order_by(Geo.geo_name).all()]


class DeleteCertificationType(Form):
    submit = SubmitField('Delete')

