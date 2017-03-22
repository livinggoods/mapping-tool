import hashlib
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager
from sqlalchemy import func, Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from data import data

##############################
class Application(db.Model):
    __tablename__ = 'application'

    id = Column(Integer, primary_key=True)
    f_name = Column(String(45))
    m_name = Column(String(45))
    l_name = Column(String(45))
    referral_id = Column(ForeignKey(u'referrals.id'), index=True)
    date_added = db.Column(db.DateTime(), default=datetime.utcnow)
    location_id = Column(ForeignKey(u'location.id'), index=True)
    recruitment_id = Column(ForeignKey(u'recruitments.id'), index=True)
    education_id = Column(ForeignKey(u'education.id'), index=True)
    edu_level_id = Column(ForeignKey(u'education_level.id'), index=True)
    vht = Column(Integer)
    maths = Column(Integer, server_default=text("'0'"))
    english = Column(Integer, server_default=text("'0'"))
    about_you = Column(Integer, server_default=text("'0'"))
    total_score = Column(Integer, server_default=text("'0'"))
    gender = Column(String(2))
    date_of_birth = db.Column(db.DateTime())
    landmark = Column(String(45))
    date_moved = db.Column(db.DateTime())
    languages = Column(String(245))
    worked_brac = Column(Integer)
    brac_chp = Column(Integer)
    community_membership = Column(String(245))
    read_english = Column(Integer, server_default=text("'0'"))
    application_score = Column(Integer, server_default=text("'0'"))
    archived = Column(Integer, server_default=text("'0'"))


    edu_level = relationship(u'EducationLevel')
    education = relationship(u'Education')
    referral = relationship(u'Referral')
    location = relationship(u'Location')
    recruitment = relationship(u'Recruitments')

class ApplicationPhone(db.Model):
    __tablename__ = 'application_phones'

    id = Column(Integer, primary_key=True)
    application_id = Column(ForeignKey(u'application.id'), index=True)
    phone = Column(String(45))
    main_phone = Column(Integer, server_default=text("'0'"))
    archived = Column(Integer, server_default=text("'0'"))

    application = relationship(u'Application')


class Branch(db.Model):
    __tablename__ = 'branch'

    id = Column(Integer, primary_key=True)
    name = Column(String(45))
    location_id = Column(ForeignKey(u'location.id'), index=True)
    lat = Column(String(45))
    lon = Column(String(45))
    archived = Column(Integer, server_default=text("'0'"))

    location = relationship(u'Location')

class Chp(db.Model):
    __tablename__ = 'chp'

    id = Column(Integer, primary_key=True)
    f_name = Column(String(45))
    l_name = Column(String(45))
    m_name = Column(String(45))
    cohort_id = Column(ForeignKey(u'cohort.id'), index=True)
    phone = Column(String(45))
    branch_id = Column(ForeignKey(u'branch.id'), index=True)
    location_id = Column(ForeignKey(u'location.id'), index=True)
    chp_id = Column(String(45))
    archived = Column(Integer, server_default=text("'0'"))

    branch = relationship(u'Branch')
    cohort = relationship(u'Cohort')
    location = relationship(u'Location')

class Cohort(db.Model):
    __tablename__ = 'cohort'

    id = Column(Integer, primary_key=True)
    cohort_number = Column(String(45))
    branch_id = Column(ForeignKey(u'branch.id'), index=True)
    archived = Column(Integer, server_default=text("'0'"))

    branch = relationship(u'Branch')


class Education(db.Model):
    __tablename__ = 'education'

    id = Column(Integer, primary_key=True)
    name = Column(String(45))
    date_added = db.Column(db.DateTime(), default=datetime.utcnow)
    archived = Column(Integer, server_default=text("'0'"))


class EducationLevel(db.Model):
    __tablename__ = 'education_level'

    id = Column(Integer, primary_key=True)
    education_id = Column(ForeignKey(u'education.id'), index=True)
    level_name = Column(String(45))
    date_added = db.Column(db.DateTime(), default=datetime.utcnow)
    archived = Column(Integer, server_default=text("'0'"))

    education = relationship(u'Education')

class Interview(db.Model):
    __tablename__ = 'interview'

    id = Column(Integer, primary_key=True)
    interview = Column(String(45))
    date_taken = db.Column(db.DateTime(), default=datetime.utcnow)
    cohort_id = Column(ForeignKey(u'cohort.id'), index=True)
    archived = Column(Integer, server_default=text("'0'"))

    cohort = relationship(u'Cohort')

class InterviewScore(db.Model):
    __tablename__ = 'interview_score'

    id = Column(Integer, primary_key=True)
    selection_id = Column(ForeignKey(u'selected_applications.id'), index=True)
    date_added = db.Column(db.DateTime(), default=datetime.utcnow)
    interview_id = Column(ForeignKey(u'interview.id'), index=True)
    motivation = Column(Integer)
    community_work = Column(Integer)
    mentality = Column(Integer)
    selling = Column(Integer)
    health = Column(Integer)
    investment = Column(Integer)
    interpersonal = Column(Integer)
    commitment = Column(Integer)
    interview_total_score = Column(Integer, server_default=text("'0'"))
    special_conditions = Column(Integer, server_default=text("'0'"))
    can_join = Column(Integer, server_default=text("'0'"))
    qualify_training = Column(Integer, server_default=text("'0'")) # boolean Yes/No
    invited_training = Column(Integer, server_default=text("'0'")) # 0 = no, 1 = yes
    confirmed_attendance = Column(Integer, server_default=text("'0'")) # 0 = no, 1 = yes
    comments = Column(db.Text) # 0 = no, 1 = yes
    user_id = Column(ForeignKey(u'users.id'), index=True)
    recruitment_id = Column(ForeignKey(u'recruitments.id'), index=True, nullable=False)
    application_id = Column(ForeignKey(u'application.id'), index=True)
    location_id = Column(ForeignKey(u'location.id'), index=True)
    archived = Column(Integer, server_default=text("'0'"))

    recruitment = relationship(u'Recruitments')
    interview = relationship(u'Interview')
    application = relationship(u'Application')
    selection = relationship(u'SelectedApplication')
    location = relationship(u'Location')
    user = relationship(u'User')

class Referral(db.Model):
    __tablename__ = 'referrals'

    id = Column(Integer, primary_key=True)
    name = Column(String(45))
    phone = Column(String(45))
    title = Column(String(45))
    location_id = Column(ForeignKey(u'location.id'), index=True)
    archived = Column(Integer, server_default=text("'0'"))

    location = relationship(u'Location')

class SelectedApplication(db.Model):
    __tablename__ = 'selected_applications'

    id = Column(Integer, primary_key=True)
    application_id = Column(ForeignKey(u'application.id'), index=True)
    location_id = Column(ForeignKey(u'location.id'), index=True)
    date_selected = db.Column(db.DateTime(), default=datetime.utcnow)
    archived = Column(Integer, server_default=text("'0'"))

    application = relationship(u'Application')
    location = relationship(u'Location')


class Village(db.Model):
    __tablename__ = 'village'

    id = Column(Integer, primary_key=True)
    name = Column(String(65), nullable=False)
    location_id = Column(ForeignKey(u'location.id'), index=True)
    lat = Column(String(45))
    lon = Column(String(45))
    archived = Column(Integer, server_default=text("'0'"))

    location = relationship(u'Location')

class LocationTargets(db.Model):
    __tablename__ = 'location_targets'

    id = Column(Integer, primary_key=True)
    location_id = Column(ForeignKey(u'location.id'), nullable=True, index=True)
    recruitment_id = Column(ForeignKey(u'recruitments.id'), nullable=True, index=True)
    chps_needed = Column(Integer, server_default=text("'0'")) #the number of CHPs needed
    archived = Column(Integer, server_default=text("'0'"))

    location = relationship(u'Location')
    recruitment = relationship(u'Recruitments')

class Recruitments(db.Model):
    __tablename__ = 'recruitments'

    id = Column(Integer, primary_key=True)
    date_added = db.Column(db.DateTime(), default=datetime.utcnow)
    name = Column(String(65), nullable=True)
    archived = Column(Integer, server_default=text("'0'"))
    added_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)

    owner = relationship(u'User')

class RecruitmentUsers(db.Model):
    __tablename__ = 'recruitment_users'
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey(u'users.id'), nullable=True, index=True)
    recruitment_id = Column(ForeignKey(u'recruitments.id'), nullable=True, index=True)
    location_id = Column(ForeignKey(u'location.id'), nullable=True, index=True)
    date_joined = db.Column(db.DateTime(), default=datetime.utcnow)

    recruitment = relationship(u'Recruitments')
    user = relationship(u'User')
    location = relationship(u'Location')

class Location(db.Model):
    __tablename__ = 'location'

    id = Column(Integer, primary_key=True)
    name = Column(String(65), nullable=False)
    parent = Column(ForeignKey(u'location.id'), nullable=True, index=True)
    lat = Column(String(45))
    lon = Column(String(45))
    meta = Column(Text)
    admin_name = Column(String(45))
    code = Column(String(45))
    polygon = Column(Text)
    archived = Column(Integer, server_default=text("'0'"))

    parent1 = relationship(u'Location', remote_side=[id])
    chp_target = db.relationship('LocationTargets', backref='target', lazy='dynamic')


    @staticmethod
    def insert_locations():
        """Update or create all Geos"""
        locs = [{'name':'Kenya', 'lat':'-0.0236', 'lon':'37.9062'},
                {'name':'Uganda', 'lat':'1.3733', 'lon':'32.2903'}]
        for name in locs:
            loc = Location.query.filter_by(name=name.get('name')).first()
            if loc is None:
                loc = Location(name=name.get('name'), lat=name.get('lat'), lon=name.get('lon'), admin_name='Country')
            db.session.add(loc)
        db.session.commit()

        # create locations based on the template given
        # 
        # import the  data
        locations = data.get_locations()
        for key, value in locations.iteritems():
            # create district
            district = Location(name=key.title(), admin_name='District', parent=2)
            db.session.add(district)
            db.session.commit()
            # create county
            district_id = district.id
            for k,v in value.iteritems():
                county = Location(name=k.title(), admin_name='County', parent=district_id)
                db.session.add(county)
                db.session.commit()
                for sub_county in v:
                    s_county = Location(name=sub_county.get('name').title(), admin_name='Sub-County', parent=county.id, code=sub_county.get('number'))
                    db.session.add(s_county)
                    db.session.commit()



    def __repr__(self):
        return '<Location %r>' % self.name

##############################
class Permission:
    """
    A specific permission task is given a bit position.  Eight tasks are
    avalible because there are eight bits in a byte.
    """
    FOLLOW = int('00000001', 2)
    COMMENT = int('00000010', 2)
    WRITE_ARTICLES = int('00000100', 2)
    MODERATE_COMMENTS = int('00001000', 2)
    # TASK_TBD = int('00010000', 2)
    # TASK_TBD = int('00100000', 2)
    # TASK_TBD = int('01000000', 2)
    ADMINISTER = int('10000000', 2)  # 0xff


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')
    archived = Column(Integer, server_default=text("'0'"))

    @staticmethod
    def insert_roles():
        """Update or create all Roles."""
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),  # User Role is default
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (int('11111111', 2), False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class Geo(db.Model):
    __tablename__ = 'geos'
    id = db.Column(db.Integer, primary_key=True)
    geo_name = db.Column(db.String(20), unique=True)
    users = db.relationship('User', backref='geo', lazy='dynamic')
    archived = Column(Integer, server_default=text("'0'"))

    @staticmethod
    def insert_geos():
        """Update or create all Geos"""
        geos = ['Kenya',
                'Uganda']
        for name in geos:
            geo = Geo.query.filter_by(geo_name=name).first()
            if geo is None:
                geo = Geo(geo_name=name)
            db.session.add(geo)
        db.session.commit()

    def __repr__(self):
        return '<Geo %r>' % self.geo_name


class UserType(db.Model):
    __tablename__ = 'user_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), unique=True)
    users = db.relationship('User', backref='user_type', lazy='dynamic')
    archived = Column(Integer, server_default=text("'0'"))

    @staticmethod
    def insert_user_types():
        """Update or create all Geos"""
        types = ['Admin',
                 'HQ Staff',
                 'Branch Manager',
                 'Branch Staff']
        for type in types:
            user_type = UserType.query.filter_by(name=type).first()
            if user_type is None:
                user_type = UserType(name=type)
            db.session.add(user_type)
        db.session.commit()

    def __repr__(self):
        return '<UserType %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    app_name = db.Column(db.String(128))
    archived = Column(Integer, server_default=text("'0'"))

    # 'default' can take a function so each time a default value needs to be
    # produced, the function is called
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    geo_id = db.Column(db.Integer, db.ForeignKey('geos.id'))
    user_type_id = db.Column(db.Integer, db.ForeignKey('user_types.id'))

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        # The method seed() sets the integer starting value used in generating
        # random numbers. Call this function before calling any other random
        # module function.
        seed()
        for i in range(count):
            passwd = forgery_py.lorem_ipsum.word()
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=passwd,
                     app_name=passwd,
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            # user might not be random, in which case rollback
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['DASHBOARD_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        """
        Generate a JSON Web Signature token with an expiration.
        """
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)  # commited after end of request
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='g'):
        # match the security of the client request
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'

        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)



class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False
# Register AnonymousUser as the class assigned to 'current_user' when the user
# is not logged in.  This will enable the app to call 'current_user.can()'
# without having to first check if the user is logged in
login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    """
    Callback function required by Flask-Login that loads a User, given the
    User identifier.  Returns User object or None.
    """
    return User.query.get(int(user_id))
