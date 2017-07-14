import hashlib
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager
from sqlalchemy import func, Column, DateTime, ForeignKey, Integer, String, Text, Numeric, text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import time


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
    testing = Column(Integer)
    niaje = Column(Integer)



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

class GpsData(db.Model):
    __tablename__ = 'gps_data'

    id = Column(String(45), primary_key=True)
    chp_phone = Column(String(45))
    record_uuid = Column(String(64))
    country = Column(String(64))
    client_time = Column(Numeric)
    date_added = db.Column(db.DateTime(), default=datetime.utcnow)
    lat = Column(Float, server_default=text("'0'"))
    lon = Column(Float, server_default=text("'0'"))
    gps_on = db.Column(db.Boolean, default=False)
    activity_type = Column(String(45))
    time_to_resolve = Column(String(45))

    def to_json(self):
        json_record = {
            'id':self.id,
            'chp_phone':self.chp_phone,
            'record_uuid':self.record_uuid,
            'country':self.country,
            'client_time': float(self.client_time),
            'lat': float(self.lat),
            'lon': float(self.lon),
            'gps_on':self.gps_on,
            'activity_type':self.activity_type,
            'time_to_resolve':self.time_to_resolve
            }
        return json_record

    @staticmethod
    def from_json(json_record):
        return GpsData (
            id = json_record.get('id'),
            chp_phone = json_record.get('chp_phone'),
            record_uuid = json_record.get('record_uuid'),
            country = json_record.get('country'),
            client_time = json_record.get('client_time'),
            lat = json_record.get('lat'),
            lon = json_record.get('lon'),
            gps_on = json_record.get('gps_on'),
            activity_type = json_record.get('activity_type'),
            time_to_resolve = json_record.get('time_to_resolve'))




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
    level_type = Column(String(45))
    hierachy = Column(Integer, server_default=text("'0'"))
    country = Column(String(45), server_default=text("'UG'"))
    date_added = db.Column(db.DateTime(), default=datetime.utcnow)
    archived = Column(Integer, server_default=text("'0'"))

    @staticmethod
    def create_education():
        """Update or create all Edus"""
        # We start with UG to reflect Android data
        for i in range(1, 9):
            country = 'UG'
            hierachy = i
            level_type = ''
            name = ''
            if i > 7:
                level_type = 'tertiary'
                name = 'Tertiary'
            elif i > 1:
                name = 'S'+str((i-1))
                level_type = 'secondary'
            else:
                name = 'Less than P7'
                level_type = 'primary'
            education = Education(name=name,level_type=level_type, hierachy=hierachy,
                country=country)
            db.session.add(education)
        db.session.commit()

        for i in range(1, 8):
            country = 'KE'
            hierachy = i
            level_type = ''
            name = ''
            if i > 6:
                level_type = 'tertiary'
                name = 'Tertiary'
            elif i > 2:
                name = 'S'+str((i-2))
                level_type = 'secondary'
            elif i == 2:
                name = 'P'+str((i+6))
                level_type = 'primary'
            else:
                name = 'Less than P7'
                level_type = 'primary'
            education = Education(name=name,level_type=level_type, hierachy=hierachy,
                country=country)
            db.session.add(education)
        db.session.commit()


class EducationLevel(db.Model):
    __tablename__ = 'education_level'

    id = Column(Integer, primary_key=True)
    education_id = Column(ForeignKey(u'education.id'), index=True)
    level_name = Column(String(45))
    date_added = db.Column(db.DateTime(), default=datetime.utcnow)
    archived = Column(Integer, server_default=text("'0'"))

    education = relationship(u'Education')

class Referral(db.Model):
    __tablename__ = 'referrals'

    id = Column(String(64), primary_key=True)
    phone = Column(String(45))
    title = Column(String(45))
    recruitment_id = Column(ForeignKey(u'recruitments.id'), nullable=True, index=True)
    name = Column(String(45))
    country = Column(String(45))
    county = Column(String(45))
    district = Column(String(45))
    subcounty = Column(String(45))
    community_unit = Column(String(45))
    village = Column(String(45))
    mapping_id = Column(ForeignKey(u'mapping.id'), nullable=True, index=True)
    lat = Column(Float, server_default=text("'0'"))
    lon = Column(Float, server_default=text("'0'"))
    mobilization = Column(String(45))
    synced = Column(String(45))
    archived = Column(Integer, server_default=text("'0'"))

    recruitment = relationship(u'Recruitments')
    mapping = relationship(u'Mapping')

    def to_json(self):
      json_record = {
        'id':self.id,
        'phone':self.phone,
        'title':self.title,
        'recruitment_id':self.recruitment_id,
        'name':self.name,
        'country':self.country,
        'county':self.county,
        'district':self.district,
        'subcounty':self.subcounty,
        'community_unit':self.community_unit,
        'village':self.village,
        'mapping_id':self.mapping_id,
        'lat':self.lat,
        'lon':self.lon,
        'mobilization':self.mobilization,
        'synced':self.synced,
        'archived':self.archived
      }
      return json_record

    @staticmethod
    def from_json(record):
      id=record.get('id')
      phone=record.get('phone')
      title=record.get('title')
      recruitment_id=record.get('recruitment_id')
      name=record.get('name')
      country=record.get('country')
      county=record.get('county')
      district=record.get('district')
      subcounty=record.get('subcounty')
      community_unit=record.get('community_unit')
      village=record.get('village')
      mapping_id=record.get('mapping_id')
      lat=record.get('lat')
      lon=record.get('lon')
      mobilization=record.get('mobilization')
      synced=record.get('synced')
      archived=record.get('archived')
      return Referral(
        id=id,
        phone=phone,
        title=title,
        recruitment_id=recruitment_id,
        name=name,
        country=country,
        county=county,
        district=district,
        subcounty=subcounty,
        community_unit=community_unit,
        village=village,
        mapping_id=mapping_id,
        lat=lat,
        lon=lon,
        mobilization=mobilization,
        synced=synced,
        archived=archived
      )

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

class Registration (db.Model):
    __tablename__ = 'registrations'

    id = Column(String(64), primary_key=True)
    name = Column(String(64), nullable=False)
    phone = Column(String(64))
    gender = Column(String(6))
    recruitment = Column(String(64), nullable=True)
    country = Column(String(16), nullable=True)
    dob = Column(Numeric)
    district = Column(String(64), nullable=True)
    subcounty = Column(String(64), nullable=True)
    division = Column(String(64), nullable=True)
    village = Column(String(64), nullable=True)
    feature = Column(String(128), nullable=True)
    english = Column(Integer, server_default=text("'0'"))
    date_moved = Column(Integer, nullable=True)
    languages = Column(String(128), nullable=True)
    brac = Column(Integer, server_default=text("'0'"))
    brac_chp = Column(Integer, server_default=text("'0'"))
    education = Column(ForeignKey(u'education.id'), nullable=True, index=True)
    occupation = Column(String(128), nullable=True)
    community_membership = Column(Integer, server_default=text("'0'"))
    added_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
    comment = Column(Text)
    proceed = Column(Integer, server_default=text("'0'"))
    client_time = Column(Numeric)
    date_added = db.Column(db.DateTime(), default=datetime.utcnow)
    synced = Column(Integer, server_default=text("'0'"))
    archived = Column(Integer, server_default=text("'0'"))
    chew_name = Column(String(128), nullable=True)
    chew_number = Column(String(128), nullable=True)
    ward = Column(String(128), nullable=True)
    cu_name = Column(String(128), nullable=True)
    link_facility = Column(String(128), nullable=True)
    households = Column(Integer, server_default=text("'0'"))
    trainings = Column(String(128), nullable=True)
    is_chv = Column(Integer, server_default=text("'0'"))
    is_gok_trained = Column(Integer, server_default=text("'0'"))
    referral = Column(String(128), nullable=True)
    referral_number = Column(String(128), nullable=True)
    referral_title = Column(String(128), nullable=True)
    vht = Column(Integer, server_default=text("'0'"))
    parish = Column(String(128), nullable=True)
    financial_accounts = Column(Integer, server_default=text("'0'"))
    recruitment_transport = Column(Integer, server_default=text("'0'"))
    branch_transport = Column(Integer, server_default=text("'0'"))

    owner = relationship(u'User')
    education_level = relationship(u'Education')

    def age(self):
        birthdate = datetime.strptime(self.date_of_birth(), '%Y-%b-%d')
        age_years = ((datetime.today() - birthdate).days/365)
        return age_years

    def date_of_birth(self):
        return time.strftime('%Y-%b-%d', time.localtime(self.dob / 1000))

    def date_client(self):
        return datetime.fromtimestamp(self.client_time / 1000).strftime('%Y-%b-%d %H:%M:%S')

    def to_json(self):
        exam = Exam.query.filter_by(applicant=self.id)
        interview = Interview.query.filter_by(archived=0, applicant=self.id)

        json_record = {
            'id':self.id,
            'name':self.name,
            'phone':self.phone,
            'gender':self.gender,
            'exam': [e.to_json() for e in exam],
            'interview': [i.to_json() for i in interview],
            'recruitment':self.recruitment,
            'country':self.country,
            'dob': float(self.dob),
            'district':self.district,
            'subcounty':self.subcounty,
            'division':self.division,
            'village':self.village,
            'feature':self.feature,
            'english':self.english,
            'date_moved':self.date_moved,
            'languages':self.languages,
            'brac':self.brac,
            'brac_chp':self.brac_chp,
            'education':self.education,
            'occupation':self.occupation,
            'community_membership':self.community_membership,
            'added_by':self.added_by,
            'comment':self.comment,
            'proceed':self.proceed,
            'client_time':float(self.client_time),
            'date_added':self.date_added,
            'synced':self.synced,
            'chew_name' : self.chew_name,
            'chew_number' : self.chew_number,
            'ward' : self.ward,
            'cu_name' : self.cu_name,
            'link_facility' : self.link_facility,
            'households' : self.households,
            'trainings' : self.trainings,
            'is_chv' : self.is_chv,
            'is_gok_trained' : self.is_gok_trained,
            'referral' : self.referral,
            'referral_number' : self.referral_number,
            'referral_title' : self.referral_title,
            'vht' : self.vht,
            'parish' : self.parish,
            'financial_accounts' : self.financial_accounts,
            'recruitment_transport' : self.recruitment_transport,
            'branch_transport' : self.branch_transport
            }

        return json_record

    @staticmethod
    def from_json(json_record):
        id = json_record.get('id')
        name = json_record.get('name')
        phone = json_record.get('phone')
        gender = json_record.get('gender')
        recruitment = json_record.get('recruitment')
        country = json_record.get('country')
        dob = json_record.get('dob')
        district = json_record.get('district')
        subcounty = json_record.get('subcounty')
        division = json_record.get('division')
        village = json_record.get('village')
        feature = json_record.get('feature')
        english = json_record.get('english')
        date_moved = json_record.get('date_moved')
        languages = json_record.get('languages')
        brac = json_record.get('brac')
        brac_chp = json_record.get('brac_chp')
        education = json_record.get('education')
        occupation = json_record.get('occupation')
        community_membership = json_record.get('community_membership')
        added_by = json_record.get('added_by')
        comment = json_record.get('comment')
        proceed = json_record.get('proceed')
        client_time = json_record.get('client_time')
        synced = json_record.get('synced')
        chew_name = json_record.get('chew_name')
        chew_number = json_record.get('chew_number')
        ward = json_record.get('ward')
        cu_name = json_record.get('cu_name')
        link_facility = json_record.get('link_facility')
        households = json_record.get('households')
        trainings = json_record.get('trainings')
        is_chv = json_record.get('is_chv')
        is_gok_trained = json_record.get('is_gok_trained')
        referral = json_record.get('referral')
        referral_number = json_record.get('referral_number')
        referral_title = json_record.get('referral_title')
        vht = json_record.get('vht')
        parish = json_record.get('parish')
        financial_accounts = json_record.get('financial_accounts')
        recruitment_transport = json_record.get('recruitment_transport')
        branch_transport = json_record.get('branch_transport')
        return Registration (id = id, name = name, phone = phone, gender = gender,
            recruitment = recruitment, country = country, dob = dob,
            district = district, subcounty = subcounty, division = division,
            village = village, feature = feature, english = english,
            date_moved = date_moved, languages = languages, brac = brac,
            brac_chp = brac_chp, education = education, occupation = occupation,
            community_membership = community_membership, added_by = added_by,
            comment = comment, proceed = proceed, chew_name = chew_name,
            chew_number = chew_number, ward = ward, cu_name = cu_name,
            link_facility = link_facility, households = households,
            trainings = trainings, is_chv = is_chv, is_gok_trained = is_gok_trained,
            referral = referral, referral_number = referral_number,
            referral_title = referral_title, vht = vht, parish = parish,
            financial_accounts = financial_accounts,
            recruitment_transport = recruitment_transport,
            branch_transport = branch_transport,
            client_time = client_time, synced = synced)

class Recruitments(db.Model):
    __tablename__ = 'recruitments'

    id = Column(String(64), primary_key=True) #db.Column(db.Integer)
    name = Column(String(128), nullable=True)
    lat = Column(String(128), nullable=True)
    lon = Column(String(128), nullable=True)
    subcounty = Column(String(128), nullable=True)
    district = Column(String(128), nullable=True)
    country = Column(String(128), nullable=True)
    county = Column(String(128), nullable=True)
    division = Column(String(128), nullable=True)
    added_by = Column(ForeignKey(u'users.id'), nullable=False, index=True)
    comment = Column(Text)
    client_time = Column(Numeric)
    date_added = db.Column(db.DateTime(), default=datetime.utcnow)
    synced = Column(Integer, server_default=text("'0'"))
    archived = Column(Integer, server_default=text("'0'"))
    status = Column(String(64), nullable=False, server_default=text("'draft'"))

    owner = relationship(u'User')

    def to_json(self):
        # get the number of registrations
        registrations = Registration.query.filter_by(archived=0,recruitment=self.id)
        json_record = {
            'id' : self.id,
            'data':{'count': registrations.count(),
                    'registrations': [registration.to_json() for registration in registrations]
                    },
            'registrations': registrations.count(),
            'name' : self.name,
            'lon' : self.lon,
            'lat' : self.lat,
            'district' : self.district,
            'subcounty' : self.subcounty,
            'county' : self.county,
            'division' : self.division,
            'country' : self.country,
            'added_by' : self.added_by,
            'comment' : self.comment,
            'client_time' : float(self.client_time),
            'synced' : self.synced,
            'status': self.status
        }
        return json_record

    @staticmethod
    def from_json(json_record):
        id = json_record.get('id')
        name = json_record.get('name')
        lon = json_record.get('lon')
        lat = json_record.get('lat')
        district = json_record.get('district')
        subcounty = json_record.get('subcounty')
        county = json_record.get('county')
        division = json_record.get('division')
        country = json_record.get('country')
        added_by = json_record.get('added_by')
        comment = json_record.get('comment')
        client_time = json_record.get('client_time')
        synced = json_record.get('synced')
        return Recruitments(id=id, name=name, lon=lon,
            lat=lat, district=district, subcounty=subcounty, county=county,
            division=division, country=country, added_by=added_by, comment=comment,
            client_time=client_time, synced=synced, archived=0)

    def country_name(self):
        geo = Geo.query.filter_by(geo_code=self.country).first()
        return geo.geo_name

class Mapping(db.Model):
    __tablename__='mapping'
    id = Column(String(64), primary_key=True)
    name = Column(String(64), nullable=True)
    country = Column(String(64), nullable=True)
    county = Column(String(64), nullable=True)
    subcounty = Column(String(64), nullable=True)
    district = Column(String(64), nullable=True)
    added_by = Column(ForeignKey(u'users.id'), nullable=False, index=True)
    contact_person = Column(String(64), nullable=True)
    phone = Column(String(64), nullable=True)
    comment = Column(Text)
    synced = Column(Integer, server_default=text("'0'"))
    date_added = db.Column(db.DateTime(), default=datetime.utcnow)
    client_time = Column(Numeric)

    owner = relationship(u'User')

    def to_json(self):
        json_record ={
            'id':self.id,
            'name':self.name,
            'country':self.country,
            'county':self.county,
            'subcounty':self.subcounty,
            'district':self.district,
            'added_by':self.added_by,
            'contact_person':self.contact_person,
            'phone': self.phone,
            'comment':self.comment,
            'synced':self.synced,
            'date_added':self.date_added,
            'client_time':float(self.client_time)
        }
        return json_record

    @staticmethod
    def from_json(record):
        id=record.get('id'),
        name=record.get('name'),
        country=record.get('country'),
        county=record.get('county'),
        subcounty=record.get('subcounty'),
        district=record.get('district'),
        added_by=record.get('added_by'),
        contact_person=record.get('contact_person'),
        phone=record.get('phone'),
        comment=record.get('comment'),
        synced=record.get('synced'),
        client_time=record.get('client_time')

        return Mapping(id=id, name=name, country=country, county=county, subcounty=subcounty, district=district,
                       added_by=added_by, contact_person=contact_person,phone=phone, comment=comment, synced=synced,
                       client_time=client_time)


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

class Exam(db.Model):
    """docstring for Exam"""
    __tablename__ = 'exams'
    id = Column(String(64), primary_key=True)
    applicant = Column(ForeignKey(u'registrations.id'), nullable=True, index=True)
    recruitment = Column(ForeignKey(u'recruitments.id'), nullable=True, index=True)
    country = Column(String(64))
    math = Column(Float, server_default=text("'0'"))
    personality = Column(Float, server_default=text("'0'"))
    english = Column(Float, server_default=text("'0'"))
    added_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
    comment = Column(Text)
    client_time = Column(Numeric, nullable=True)
    date_added = db.Column(db.DateTime(), default=datetime.utcnow)
    synced = Column(Integer, server_default=text("'0'"))
    archived = Column(Integer, server_default=text("'0'"))

    registration = relationship(u'Registration')
    base_recruitment = relationship(u'Recruitments')
    user = relationship(u'User')

    def total_score(self):
        return (self.math + self.personality + self.english)

    def has_passed(self):
        if self.math == 0 or self.english == 0 or self.personality == 0:
            return False
        elif self.total_score() < 30:
            return False
        else:
            return True

    def to_json(self):
        json_record = {
            'id': self.id,
            'applicant': self.applicant,
            'recruitment': self.recruitment,
            'country': self.country,
            'math': self.math,
            'personality': self.personality,
            'english': self.english,
            'added_by': self.added_by,
            'comment': self.comment,
            'client_time': float(self.client_time),
            'synced': self.synced
        }
        return json_record

    @staticmethod
    def from_json(json_record):
        id = json_record.get('id')
        applicant = json_record.get('applicant')
        recruitment = json_record.get('recruitment')
        country = json_record.get('country')
        math = json_record.get('math')
        personality = json_record.get('personality')
        english = json_record.get('english')
        added_by = json_record.get('added_by')
        comment = json_record.get('comment')
        client_time = json_record.get('client_time')
        synced = json_record.get('synced')
        return Exam(id = id, applicant = applicant, recruitment = recruitment,
                country = country, math = math, personality = personality,
                english = english, added_by = added_by, comment = comment,
                client_time = client_time, synced = synced)


class Interview(db.Model):
    __tablename__ = 'interviews'

    id = Column(String(64), primary_key=True)
    applicant = Column(ForeignKey(u'registrations.id'), nullable=True, index=True)
    recruitment = Column(ForeignKey(u'recruitments.id'), nullable=True, index=True)
    motivation = Column(Integer, server_default=text("'0'"))
    community = Column(Integer, server_default=text("'0'"))
    mentality = Column(Integer, server_default=text("'0'"))
    country = Column(String(64), nullable=True)
    selling = Column(Integer, server_default=text("'0'"))
    health = Column(Integer, server_default=text("'0'"))
    investment = Column(Integer, server_default=text("'0'"))
    interpersonal = Column(Integer, server_default=text("'0'"))
    canjoin = Column(Integer, server_default=text("'0'"))
    commitment = Column(Integer, server_default=text("'0'"))
    total = Column(Integer, server_default=text("'0'"))
    selected = Column(Integer, server_default=text("'0'"))
    synced = Column(Integer, server_default=text("'1'"))
    added_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
    comment = Column(Text, nullable=True)
    client_time = Column(Numeric, nullable=True)
    date_added = db.Column(db.DateTime(), default=datetime.utcnow)
    archived = Column(Integer, server_default=text("'0'"))

    registration = relationship(u'Registration')
    base_recruitment = relationship(u'Recruitments')
    user = relationship(u'User')

    def total_score(self):
        return (self.motivation + self.community + self.mentality + self.selling + 
            self.health + self.investment + self.interpersonal + self.commitment)

    def has_passed(self):
        if self.total_score > 24 and self.canjoin == 1 and self.commitment > 1:
            return True
        else:
            return False

    def to_json(self):
        json_record = {
            'id': self.id,
            'applicant': self.applicant,
            'recruitment': self.recruitment,
            'motivation': self.motivation,
            'community' :self.community,
            'mentality': self.mentality,
            'country': self.country,
            'selling': self.selling,
            'health': self.health,
            'investment': self.investment,
            'interpersonal': self.interpersonal,
            'canjoin' :self.canjoin,
            'commitment': self.commitment,
            'total' :self.total,
            'selected': self.selected,
            'synced': self.synced,
            'added_by': self.added_by,
            'comment': self.comment,
            'date_added': self.date_added,
        }
        return json_record

    @staticmethod
    def from_json(json_record):
        id = json_record.get('id')
        applicant = json_record.get('applicant')
        recruitment = json_record.get('recruitment')
        motivation = json_record.get('motivation')
        community = json_record.get('community')
        mentality = json_record.get('mentality')
        country = json_record.get('country')
        selling = json_record.get('selling')
        health = json_record.get('health')
        investment = json_record.get('investment')
        interpersonal = json_record.get('interpersonal')
        canjoin = json_record.get('canjoin')
        commitment = json_record.get('commitment')
        total = json_record.get('total')
        selected = json_record.get('selected')
        synced = json_record.get('synced')
        added_by = json_record.get('added_by')
        comment = json_record.get('comment')
        client_time = json_record.get('client_time')
        return Interview (id = id, applicant = applicant, recruitment = recruitment,
            motivation = motivation, community = community, mentality = mentality,
            country = country, selling = selling, health = health, investment = investment,
            interpersonal = interpersonal, canjoin = canjoin, commitment = commitment,
            total = total, selected = selected, synced = synced, added_by = added_by,
            comment = comment, client_time = client_time)


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
    country = Column(String(45))
    polygon = Column(Text)
    archived = Column(Integer, server_default=text("'0'"))

    parent1 = relationship(u'Location', remote_side=[id])
    chp_target = db.relationship('LocationTargets', backref='target', lazy='dynamic')

    def to_json(self):
        json_record = {
            'id' : self.id,
            'name' : self.name,
            'parent' : self.parent,
            'lat' : self.lat,
            'country': self.country,
            'lon' : self.lon,
            'meta' : self.meta,
            'admin_name' : self.admin_name,
            'code' : self.code,
            'polygon' : self.polygon,
            'archived' : self.archived,
        }
        return json_record


    @staticmethod
    def insert_locations():
        """Update or create all Geos"""
        locs = [{'name':'Kenya', 'lat':'-0.0236', 'lon':'37.9062'},
                {'name':'Uganda', 'lat':'1.3733', 'lon':'32.2903'}]
        for name in locs:
            loc = Location.query.filter_by(name=name.get('name')).first()
            if loc is None:
                loc = Location(name=name.get('name'), country='UG', lat=name.get('lat'), lon=name.get('lon'), admin_name='Country')
            db.session.add(loc)
        db.session.commit()

        # create locations based on the template given
        # 
        # import the  data
        locations = data.get_locations()
        for key, value in locations.iteritems():
            # create district
            district = Location(name=key.title(), country='UG', admin_name='District', parent=2)
            db.session.add(district)
            db.session.commit()
            # create county
            district_id = district.id
            for k,v in value.iteritems():
                county = Location(name=k.title(), country='UG', admin_name='County', parent=district_id)
                db.session.add(county)
                db.session.commit()
                for sub_county in v:
                    s_county = Location(name=sub_county.get('name').title(), admin_name='Sub-County', country='UG', parent=county.id, code=sub_county.get('number'))
                    db.session.add(s_county)
                    db.session.commit()
        #KENYA
        counties = data.get_ke_counties()
        for county in counties:
            loc = Location(name=county.get('name'), country='KE', code=county.get('code'), admin_name='County', parent=1)
            db.session.add(loc)
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
    geo_code = db.Column(db.String(20))
    users = db.relationship('User', backref='geo', lazy='dynamic')
    archived = Column(Integer, server_default=text("'0'"))

    @staticmethod
    def insert_geos():
        """Update or create all Geos"""
        geos = [{'name':'Kenya', 'code':'KE'},
                {'name':'Uganda', 'code':'UG'}]
        for geo in geos:
            added_geo = Geo.query.filter_by(geo_name=geo['name']).first()
            if added_geo is None:
                geo = Geo(geo_name=geo['name'], geo_code=geo['code'])
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

def get_country_name(code):
    if code=="KE":
        return "Kenya"
    else:
        return "Uganda"