import hashlib
import time
from collections import OrderedDict
from datetime import datetime
from random import randint
import uuid

import redis
import rq
from flask import current_app, request, json
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Numeric, text, Float, inspect
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from data import data

from utils.utils import validate_uuid, asdict
from . import db, login_manager


##############################

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

    id = Column(String(64), primary_key=True)
    branch_name = Column(String(45))
    lat = Column(Float, server_default=text("'0.0'"))
    lon = Column(Float, server_default=text("'0.0'"))
    archived = Column(Integer, server_default=text("'0'"))
    country = Column(String(64))
    county_id = Column(String(65), nullable=True)
    subcounty_id = Column(String(65), nullable=True)


class Cohort(db.Model):
    __tablename__ = 'cohort'

    id = Column(Integer, primary_key=True)
    cohort_number = Column(String(45))
    cohort_name = Column(String(45)) # e.g. 1BUS for Busia
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
    
    def to_json(self):
      json_record = {
        '_id' : self.id,
        'name' : self.name,
        'level_type' : self.level_type,
        'hierachy' : self.hierachy,
        'country' : self.country,
        'date_added' : self.date_added,
        'archived' : self.archived,
      }
      return json_record

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
      
      referral = Referral()
  
      for k, v in record.iteritems():
        if k == 'lat' or k == 'lon':
          v = float(v) if bool(v) else float(0)
          
        if k == 'mapping' or k == 'recruitment':
          setattr(referral, '%s_id'%k, v)
          continue
        
        setattr(referral, k, v)

      if referral.id is None:
        return None

      return referral

class Village(db.Model):
    __tablename__ = 'village'

    id = Column(String(65), primary_key=True)
    village_name = Column(String(64), nullable=True)
    mapping_id = Column(ForeignKey(u'mapping.id'), index=True)
    lat = Column(Float, server_default=text("'0'"), nullable=False)
    lon = Column(Float, server_default=text("'0'"), nullable=False)
    country = Column(String(65), nullable=True)
    district = Column(String(65), nullable=True)
    county = Column(String(65),nullable=True)
    sub_county_id = Column(String(65), nullable=True)
    parish_id = Column(ForeignKey(u'parish.id'), index=True)
    community_unit_id = Column(ForeignKey(u'community_unit.id'), index=True)
    ward = Column(String(65), nullable=True)
    link_facility_id = Column(ForeignKey(u'link_facility.id'), index=True)
    area_chief_name = Column(String(65), nullable=True)
    area_chief_phone = Column(String(65), nullable=True)
    distancetobranch = Column(Float, server_default=text("'0'"), nullable=False)
    transportcost = Column(Float, server_default=text("'0'"), nullable=False)
    distancetomainroad = Column(Float, server_default=text("'0'"), nullable=False)
    noofhouseholds = Column(Float, server_default=text("'0'"), nullable=False)
    mohpoplationdensity = Column(Float, server_default=text("'0'"), nullable=False)
    estimatedpopulationdensity = Column(Float, server_default=text("'0'"), nullable=False)
    economic_status = Column(String(65), nullable=True)
    distancetonearesthealthfacility = Column(Float, server_default=text("'0'"),nullable=False)
    actlevels = Column(Float, server_default=text("'0'"),nullable=False)
    actprice = Column(Float, server_default=text("'0'"), nullable=False)
    mrdtlevels = Column(Float, server_default=text("'0'"), nullable=False)
    mrdtprice = Column(Float, server_default=text("'0'"), nullable=False)
    presenceofhostels = Column(Integer, server_default=text("'0'"),nullable=False)
    presenceofestates = Column(Integer, server_default=text("'0'"), nullable=False)
    number_of_factories = Column(Float, server_default=text("'0'"), nullable=False)
    presenceofdistibutors = Column(Integer, server_default=text("'0'"), nullable=False)
    name_of_distibutors = Column(Text, nullable=True)
    tradermarket = Column(Integer, server_default=text("'0'"), nullable=False)
    largesupermarket = Column(Integer, server_default=text("'0'"), nullable=False)
    ngosgivingfreedrugs = Column(Integer, server_default=text("'0'"), nullable=False)
    ngodoingiccm = Column(Integer, server_default=text("'0'"), nullable=False)
    ngodoingmhealth = Column(Integer, server_default=text("'0'"), nullable=False)
    nameofngodoingiccm = Column(Text, nullable=True)
    nameofngodoingmhealth = Column(Text, nullable=True)
    privatefacilityforact = Column(Text, nullable=True)
    privatefacilityformrdt = Column(Text, nullable=True)
    synced = Column(Integer, server_default=text("'0'"), nullable=False)
    chvs_trained = Column(Integer, server_default=text("'0'"), nullable=False)
    client_time = Column(Numeric, nullable=True)
    date_added = db.Column(db.DateTime(), default=datetime.utcnow)
    archived = Column(Integer, server_default=text("'0'"))
    addedby = Column(ForeignKey(u'users.id'), nullable=True, index=True)
    comment = Column(Text, nullable=True)
    brac_operating = Column(Integer, server_default=text("'0'"), nullable=False)
    mtn_signal = Column(Integer, server_default=text("'0'"), nullable=False)
    safaricom_signal = Column(Integer, server_default=text("'0'"), nullable=False)
    airtel_signal = Column(Integer, server_default=text("'0'"), nullable=False)
    orange_signal = Column(Integer, server_default=text("'0'"), nullable=False)
    act_stock = Column(Integer, server_default=text("'0'"), nullable=False)
    
    mapping = relationship(u'Mapping')
    parish = relationship(u'Parish')
    community_unit = relationship(u'CommunityUnit')
    link_facility = relationship(u'LinkFacility')
    user = relationship(u'User')
    
    def village_index_score(self):
      score = 0
      score = (self.distance_to_branch_score() + self.est_cost_of_transport_score() +
               self.distance_to_main_road_score() + self.number_of_hh_score() +
               self.est_population_density_score() + self.area_economic_status_score() +
               self.distance_to_health_facility_score() + self.stock_level_for_act_score() +
               self.cost_of_act_score() + self.presence_of_estates_score() +
               self.presence_of_factories_score() + self.presence_of_universities_score() +
               self.presence_of_distributors_score() + self.presence_trader_market_score() +
               self.presence_large_supermarket_score() +
               self.presence_of_ngo_distributing_free_drugs_score() +
               self.presence_of_partner_ngos_score() + self.mtn_connectivity_score())
      return score
    
    def chps_to_recruit(self):
      if self.economic_status =="Rural":
          return int(round(self.noofhouseholds /150))
      elif self.economic_status =="Urban/informal":
        return int(round(self.noofhouseholds / 150))
      else:
        return int(round(self.noofhouseholds / 400))
    
    def distance_to_branch_score(self):
      score = 0
      if self.distancetobranch < 5:
        score = 5
      elif self.distancetobranch < 10:
        score = 3
      else:
        score =0
      return score
    
    def est_cost_of_transport_score(self):
      score = 0
      if self.transportcost < 2500:
        score=15
      elif self.transportcost < 5000:
        score = 8
      else:
        score =0
      return score
    
    def distance_to_main_road_score(self):
      score = 0
      if self.distancetomainroad < 2:
        score = 0
      elif self.distancetomainroad < 5:
        score =0
      else:
        score =0
      return score
    
    
    def number_of_hh_score(self):
      score =  0
      if self.noofhouseholds >= 150:
        score =4
      else:
        score =-100
      return score
    
    
    def est_population_density_score(self):
      score =  0
      if self.economic_status == 'Rural':
        score = 3
      elif self.economic_status == 'Urban/informal':
        score=5
      else:
        score = 0
      return score
    
    
    def area_economic_status_score(self):
      score = 0
      if self.economic_status == 'Urban / Upper Income':
        score = -100
      elif self.economic_status == 'Rural':
        score = 3
      else:
        score = 5
      return score
    
    
    def distance_to_health_facility_score(self):
      if self.distancetonearesthealthfacility < 2:
        score = 0
      elif self.distancetonearesthealthfacility < 5:
        score = 3
      else:
        score = 5
      return score
    
    
    def stock_level_for_act_score(self):
      score =0
      if self.act_stock < 1:
        score = 10
      else:
        score = 0
      return score
    
    
    def cost_of_act_score(self):
      score = 0
      if self.actprice > 6000:
        score = 10
      elif self.actprice > 3000:
        score = 5
      else:
        score = 0
      return score
    
    def presence_of_estates_score(self):
      if self.presenceofestates ==0:
        score = 2
      else:
        score = 0
      return score
    
    
    def presence_of_factories_score(self):
      if self.number_of_factories == 0:
        score = 2
      elif self.number_of_factories < 2:
        score = 1
      else:
        score = 0
      return score
    
    
    def presence_of_universities_score(self):
      if self.presenceofhostels == 0:
        score = 2
      else:
        score = 0
      return score
    
    
    def presence_of_distributors_score(self):
      score = 0
      if self.presenceofdistibutors == 0:
        score = 2
      elif self.presenceofdistibutors <= 2:
        score = 1
      else:
        score = 0
      return score
    def presence_trader_market_score(self):
      score = 0
      if self.tradermarket ==0:
        score = 2
      else:
        score =0
      return score
    
    
    def presence_large_supermarket_score(self):
      score = 0
      if self.largesupermarket == 0:
        score = 2
      else:
        score = 0
      return score
    
    def presence_of_ngo_distributing_free_drugs_score(self):
      score = 0
      if self.ngosgivingfreedrugs == 0:
        score = 10
      else:
        score = 0
      return score
    
    
    def presence_of_partner_ngos_score(self):
      score = 0
      if self.ngodoingiccm == 0:
        score = 5
      else:
        score = 0
      return score
    
    
    def which_ones_score(self):
      return 0
    
    def mtn_connectivity_score(self):
      score = 0
      if self.mtn_signal > 3:
        score = 5
      else:
        score = 0
      return score
    
    def to_json(self):
      json_record={
        'id':self.id,
        'village_name':self.village_name,
        'mapping_id':self.mapping_id,
        'lat':self.lat,
        'lon':self.lon,
        'country':self.country,
        'district':self.district,
        'county':self.county,
        'sub_county_id':self.sub_county_id,
        'parish':self.parish_id,
        'community_unit':self.community_unit_id,
        'ward':self.ward,
        'link_facility_id':self.link_facility_id,
        'area_chief_name':self.area_chief_name,
        'area_chief_phone':self.area_chief_phone,
        'distancetobranch':self.distancetobranch,
        'transportcost':self.transportcost,
        'distancetomainroad':self.distancetomainroad,
        'noofhouseholds':self.noofhouseholds,
        'mohpoplationdensity':self.mohpoplationdensity,
        'estimatedpopulationdensity':self.estimatedpopulationdensity,
        'economic_status':self.economic_status,
        'distancetonearesthealthfacility':self.distancetonearesthealthfacility,
        'actlevels':self.actlevels,
        'actprice':self.actprice,
        'mrdtlevels':self.mrdtlevels,
        'mrdtprice':self.mrdtprice,
        'presenceofhostels':self.presenceofhostels,
        'presenceofestates':self.presenceofestates,
        'number_of_factories':self.number_of_factories,
        'presenceofdistibutors':self.presenceofdistibutors,
        'name_of_distibutors':self.name_of_distibutors,
        'tradermarket':self.tradermarket,
        'largesupermarket':self.largesupermarket,
        'ngosgivingfreedrugs':self.ngosgivingfreedrugs,
        'ngodoingiccm':self.ngodoingiccm,
        'ngodoingmhealth':self.ngodoingmhealth,
        'nameofngodoingiccm':self.nameofngodoingiccm,
        'nameofngodoingmhealth':self.nameofngodoingmhealth,
        'privatefacilityforact':self.privatefacilityforact,
        'privatefacilityformrdt':self.privatefacilityformrdt,
        'synced':self.synced,
        'chvs_trained':self.chvs_trained,
        'date_added':self.date_added,
        'addedby':self.addedby,
        'comment':self.comment,
        'brac_operating':self.brac_operating,
        'mtn_signal':self.mtn_signal,
        'safaricom_signal':self.safaricom_signal,
        'airtel_signal':self.airtel_signal,
        'orange_signal':self.orange_signal,
        'act_stock':self.act_stock,
        'dateadded': self.client_time
      }
      return json_record


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
    occupation = Column(String(1024), nullable=True)
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
    referral_id = Column(ForeignKey(u'referrals.id'), nullable=True, index=True)
    assets_tracker_data = Column(Text)
    posted_to_assets_tracker = db.Column(db.Boolean, default=False, index=True)
    other = db.Column(db.Text, nullable=True, server_default=text("'{}'"))

    owner = relationship(u'User')
    education_level = relationship(u'Education')
    chew_referral = relationship(u'Referral')

    def age(self):
        birthdate = datetime.strptime(self.date_of_birth(), '%Y-%b-%d')
        age_years = ((datetime.today() - birthdate).days/365)
        return age_years

    def date_of_birth(self):
        return time.strftime('%Y-%b-%d', time.localtime(self.dob / 1000))

    def date_client(self):
        return datetime.fromtimestamp(self.client_time / 1000).strftime('%Y-%b-%d %H:%M:%S')
    
    def get_recruitment(self):
        if self.recruitment:
            try:
                recruitment = Recruitments.query.filter_by(id=self.recruitment).first()
                
                return recruitment.name
            except Exception as e:
                pass
        return self.recruitment

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
            'dob': float(self.dob) if self.dob else self.dob,
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
            'education_details':self.education_level.to_json(),
            'occupation':self.occupation,
            'community_membership':self.community_membership,
            'added_by':self.added_by,
            'comment':self.comment,
            'proceed':self.proceed,
            'client_time':float(self.client_time) if self.client_time else None,
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
            'branch_transport' : self.branch_transport,
            'referral_id' : self.referral_id,
            # 'other': self.other TODO findout how to add this
            }
        if self.chew_referral is not None:
          json_record['referral_details'] = self.chew_referral.to_json()
        else:
          json_record['referral_details']={}

        return json_record

    @staticmethod
    def from_json(json_record):
      return Registration (
        id = json_record.get('id'),
        name = json_record.get('name') if json_record.get('name') is
                                          not None or json_record.get('name') != '' else None,
        phone = json_record.get('phone') if json_record.get('phone') is not None or json_record.get('phone') != '' else None,
        gender = json_record.get('gender') if json_record.get('gender') is not None or json_record.get('gender') != '' else None,
        dob = json_record.get('dob') if json_record.get('dob') is not None or json_record.get('dob') != '' else None,
        district = json_record.get('district') if json_record.get('district') is not None or json_record.get('district') != '' else None,
        subcounty = json_record.get('subcounty') if json_record.get('subcounty') is not None or json_record.get('subcounty') != '' else None,
        recruitment = json_record.get('recruitment') if json_record.get('recruitment') is not None or json_record.get('recruitment') != '' else None,
        country = json_record.get('country') if json_record.get('country') is not None or json_record.get('country') != '' else None,
        division = json_record.get('division') if json_record.get('division') is not None or json_record.get('division') != '' else None,
        village = json_record.get('village') if json_record.get('village') is not None or json_record.get('village') != '' else None,
        feature = json_record.get('feature') if json_record.get('feature') is not None or json_record.get('feature') != '' else None,
        english = json_record.get('english') if json_record.get('english') is not None or json_record.get('english') != '' else None,
        date_moved = json_record.get('date_moved') if json_record.get('date_moved') is not None or json_record.get('date_moved') != '' else None,
        languages = json_record.get('languages') if json_record.get('languages') is not None or json_record.get('languages') != '' else None,
        brac = json_record.get('brac') if json_record.get('brac') is not None or json_record.get('brac') != '' else None,
        brac_chp = json_record.get('brac_chp') if json_record.get('brac_chp') is not None or json_record.get('brac_chp') != '' else None,
        education = json_record.get('education') if json_record.get('education') is not None or json_record.get('education') != '' else None,
        occupation = json_record.get('occupation') if json_record.get('occupation') is not None or json_record.get('occupation') != '' else None,
        community_membership = json_record.get('community_membership') if json_record.get('community_membership') is not None or json_record.get('community_membership') != '' else None,
        added_by = json_record.get('added_by') if json_record.get('added_by') is not None or json_record.get('added_by') != '' else None,
        comment = json_record.get('comment') if json_record.get('comment') is not None or json_record.get('comment') != '' else None,
        proceed = json_record.get('proceed') if json_record.get('proceed') is not None or json_record.get('proceed') != '' else None,
        client_time = json_record.get('client_time') if json_record.get('client_time') is not None or json_record.get('client_time') != '' else None,
        chew_name = json_record.get('chew_name') if json_record.get('chew_name') is not None or json_record.get('chew_name') != '' else None,
        chew_number = json_record.get('chew_number') if json_record.get('chew_number') is not None or json_record.get('chew_number') != '' else None,
        ward = json_record.get('ward') if json_record.get('ward') is not None or json_record.get('ward') != '' else None,
        cu_name = json_record.get('cu_name') if json_record.get('cu_name') is not None or json_record.get('cu_name') != '' else None,
        link_facility = json_record.get('link_facility') if json_record.get('link_facility') is not None or json_record.get('link_facility') != '' else None,
        households = json_record.get('households') if json_record.get('households') is not None or json_record.get('households') != '' else None,
        trainings = json_record.get('trainings') if json_record.get('trainings') is not None or json_record.get('trainings') != '' else None,
        is_chv = json_record.get('is_chv') if json_record.get('is_chv') is not None or json_record.get('is_chv') != '' else None,
        is_gok_trained = json_record.get('is_gok_trained') if json_record.get('is_gok_trained') is not None or json_record.get('is_gok_trained') != '' else None,
        referral = json_record.get('referral') if json_record.get('referral') is not None or json_record.get('referral') != '' else None,
        referral_title = json_record.get('referral_title') if json_record.get('referral_title') is not None or json_record.get('referral_title') != '' else None,
        referral_number = json_record.get('referral_number') if json_record.get('referral_number') is not None or json_record.get('referral_number') != '' else None,
        vht = json_record.get('vht') if json_record.get('vht') is not None or json_record.get('vht') != '' else None,
        parish = json_record.get('parish') if json_record.get('parish') is not None or json_record.get('parish') != '' else None,
        financial_accounts = json_record.get('financial_accounts') if json_record.get('financial_accounts') is not None or json_record.get('financial_accounts') != '' else None,
        recruitment_transport = json_record.get('recruitment_transport') if json_record.get('recruitment_transport') is not None or json_record.get('recruitment_transport') != '' else None,
        branch_transport = json_record.get('branch_transport') if json_record.get('branch_transport') is not None or json_record.get('branch_transport') != '' else None,
        referral_id = json_record.get('chew_id') if json_record.get('chew_id') is not None or json_record.get('chew_id') != '' else None,
        synced = json_record.get('synced') if json_record.get('synced') is not None or json_record.get('synced') != '' else None,
        archived = 0,
          other=json_record.get('other') if json_record.get('other') else None
        )
    

class Parish(db.Model):
    __tablename__ = 'parish'
    
    id = Column(String(64), primary_key=True, nullable=False)
    name = Column(String(64), nullable=False)
    parent = Column(String(64), nullable=True)
    mapping_id = Column(ForeignKey(u'mapping.id'), nullable=True, index=True)
    added_by = Column(ForeignKey(u'users.id'), nullable=False, index=True)
    contact_person = Column(String(64), nullable=True)
    phone = Column(String(64), nullable=True)
    comment = Column(Text)
    synced = Column(Integer, server_default=text("'0'"))
    country = Column(String(64), nullable=True)
    client_time = Column(Numeric)
    date_added = db.Column(db.DateTime(), default=datetime.utcnow)
    archived = Column(Integer, server_default=text("'0'"))

    mapping = relationship(u'Mapping')
    user = relationship(u'User')
    
    def to_dict(self):
      return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
    
    def to_json(self):
      json_record={
        'id':self.id if self.id is not None else None,
        'name':self.name if self.name is not None else None,
        'parent':self.parent if self.parent is not None else None,
        'mapping_id':self.mapping_id if self.mapping_id else None,
        'mapping': self.mapping.to_json() if self.mapping_id and self.mapping else None,
        'added_by':self.added_by if self.added_by is not None else None,
        'contact_person':self.contact_person if self.contact_person is not None else None,
        'phone':self.phone if self.phone is not None else None,
        'comment':self.comment if self.comment is not None else None,
        'synced':self.synced if self.synced is not None else None,
        'country':self.country if self.country is not None else None,
        'client_time':float(self.client_time) if bool(self.client_time) else None,
        'date_added':self.date_added if self.date_added is not None else None
      }
      return json_record


class Partner(db.Model):
    __tablename__ = 'partner'
    
    id = Column(String(64), primary_key=True, nullable=False)
    name = Column(String(64), nullable=False)
    contact_person = Column(String(64), nullable=True)
    contact_person_phone = Column(String(64), nullable=True)
    parent = Column(String(64), nullable=True)
    mapping_id = Column(ForeignKey(u'mapping.id'), nullable=True, index=True)
    client_time = Column(Numeric)
    date_added = db.Column(db.DateTime(), default=datetime.utcnow)
    added_by = Column(ForeignKey(u'users.id'), nullable=False, index=True)
    synced = Column(String(64), nullable=True)
    country = Column(String(64), nullable=True)
    comment = Column(String(64), nullable=True)
    archived = Column(Integer, server_default=text("'0'"))
    
    user = relationship(u'User')
    mapping = relationship(u'Mapping')
    
    @staticmethod
    def from_json(json):
      pa = Partner()
      for k, v in json.iteritems():
        if v != '':
          setattr(pa, k, v)
      return pa
    
    def to_json(self):
      json_record={
        'id':self.id,
        'name':self.name,
        'contact_person':self.contact_person,
        'contact_person_phone':self.contact_person_phone,
        'parent':self.parent,
        'mapping_id':self.mapping_id,
        'mapping':self.mapping.to_json(),
        'client_time':float(self.client_time),
        'date_added':self.date_added,
        'added_by':self.added_by,
        'synced':self.synced,
        'country':self.country,
        'comment':self.comment
      }
      return json_record


class PartnerActivity(db.Model): # @TODO create an endpoint that we can use to check if the partner working in the area
    __tablename__ = 'partner_activity'
    
    id = Column(String(64), primary_key=True, nullable=False)
    partner_id = Column(ForeignKey(u'partner.id'), nullable=True, index=True)
    country = Column(String(64), nullable=True)
    county_id = Column(String(64), nullable=True)
    sub_county_id = Column(String(64), nullable=True)
    parish_id = Column(String(64), nullable=True)
    village_id = Column(ForeignKey(u'village.id'), nullable=True, index=True)
    community_unit_id = Column(ForeignKey(u'community_unit.id'), nullable=True, index=True)
    mapping_id = Column(ForeignKey(u'mapping.id'), nullable=True, index=True)
    comment = Column(String(64), nullable=True)
    doing_mhealth = Column(Integer, nullable=True)
    doing_iccm = Column(Integer, nullable=True)
    giving_free_drugs = Column(Integer, nullable=True)
    giving_stipend = Column(Integer, nullable=True)
    date_added = db.Column(db.DateTime(), default=datetime.utcnow)
    client_time = Column(Numeric)
    added_by = Column(ForeignKey(u'users.id'), nullable=False, index=True)
    activities = Column(Text)
    synced = Column(Integer, server_default=text("'0'"))
    archived = Column(Integer, server_default=text("'0'"))
    other = Column(Text, nullable=True, server_default=text("'{}'"))
    
    user = relationship(u'User')
    mapping = relationship(u'Mapping')
    village = relationship(u'Village')
    community_unit = relationship(u'CommunityUnit')
    partner = relationship(u'Partner')

    @staticmethod
    def from_json(json):
      pa = PartnerActivity()
      for k, v in json.iteritems():
        if k == 'date_added':
          continue
        else:
          if v != '':
            setattr(pa, k, v)
      return pa
    
    def to_json(self):
      json_record={
        'id':self.id,
        'partner_id':self.partner_id,
        'partner':self.partner.to_json(),
        'country':self.country,
        'county_id':self.county_id,
        'sub_county_id':self.sub_county_id,
        'parish_id':self.parish_id,
        'parish':self.parish.to_json(),
        'village_id':self.village_id,
        'village':self.village.to_json(),
        'community_unit_id':self.community_unit_id,
        'community_unit':self.community_unit.to_json(),
        'mapping_id':self.mapping_id,
        'mapping':self.mapping.to_json(),
        'comment':self.comment,
        'doing_mhealth':self.doing_mhealth,
        'doing_iccm':self.doing_iccm,
        'giving_free_drugs':self.giving_free_drugs,
        'giving_stipend':self.giving_stipend,
        'date_added':self.date_added,
        'client_time':self.client_time,
        'added_by':self.added_by,
        'activities':self.activities,
        'synced':self.synced,
        'archived':self.archived,
        'other': self.other
      }
      return json_record


class IccmComponents(db.Model):
  __tablename__ = 'iccm_components'
  
  id = db.Column(db.Integer, primary_key=True)
  component_name = Column(String(128), nullable=True)
  added_by = Column(ForeignKey(u'users.id'), nullable=False, index=True)
  comment = Column(Text)
  client_time = Column(Numeric)
  date_added = db.Column(db.DateTime(), default=datetime.utcnow)
  archived = Column(Integer, server_default=text("'0'"))
  status = Column(String(64), nullable=False, server_default=text("'draft'"))
  
  user = relationship(u'User')
  
  def to_json(self):
    json_record={
      'id':self.id,
      'component_name':self.component_name,
      'added_by':self.added_by,
      'user':self.user.to_json(),
      'comment':self.comment,
      'client_time':float(self.client_time),
      'date_added':self.date_added,
      'archived':self.archived,
      'status':self.status
    }
    return json_record


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
    county_id = Column(ForeignKey(u'ke_county.id'), nullable=True, index=True)
    subcounty_id = Column(ForeignKey(u'subcounty.id'), nullable=True, index=True)
    location_id = Column(ForeignKey(u'location.id'), nullable=True, index=True)
    posted_to_assets_tracker = db.Column(db.Boolean, default=False, index=True)
    cohort_id = db.Column(ForeignKey(u'cohort.id'), nullable=True)
    
    owner = relationship(u'User')
    cohort = relationship(u'Cohort')

    def to_json(self):
        # get the number of registrations
        registrations = Registration.query.filter_by(archived=0,recruitment=self.id)
        sub_county_details = SubCounty.query.filter_by(id=self.subcounty).first()
        subcounty=''
        if sub_county_details is None:
            if not validate_uuid(self.subcounty):
              subcounty = self.subcounty
        else:
          subcounty = sub_county_details.name
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
            'subcounty' : subcounty,
            'subcounty_details' : sub_county_details.to_json() if sub_county_details is not None else {},
            'county' : self.county,
            'division' : self.division,
            'country' : self.country,
            'added_by' : self.added_by,
            'comment' : self.comment,
            'client_time' : float(self.client_time) if self.client_time else None,
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
    archived = Column(Integer, server_default=text("'0'"))

    owner = relationship(u'User')
    
    def to_dict(self):
      return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

    def to_json(self):
        if self.country =="KE":
          county = County.query.filter_by(id=self.county).first()
          subcounty= SubCounty.query.filter_by(id=self.county).first()
        else:
          county= Location.query.filter_by(id=self.county).first()
          if self.subcounty:
            subcounty= Location.query.filter_by(id=self.subcounty).first()
          else:
            subcounty = None

        county_name = county.name if county is not None else None
        subcounty_name = subcounty.name if subcounty is not None else None
        
        json_record ={
            'id':self.id,
            'name':self.name,
            'country':self.country,
            'county':self.county,
            'subcounty':self.subcounty,
            'county_name':county_name,
            'sub_county_name': subcounty_name,
            'district':self.district,
            'added_by':self.added_by,
            'contact_person':self.contact_person,
            'phone': self.phone,
            'comment':self.comment,
            'synced':self.synced,
            'date_added': long(time.mktime(self.date_added.timetuple())) if self.date_added else long(0),
            'client_time':float(self.client_time) if self.client_time else None
        }
        return json_record

    @staticmethod
    def from_json(record):
        id = record.get('id', None)
        if id:
            if id.startswith('['):
                id = json.loads(id)[0]
        record['id'] = id
        
        mapping = Mapping()
        for k, v in record.iteritems():
          if k == 'date_added':
            continue
          else:
            setattr(mapping, k, v)
        
        return mapping


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


class CommunityUnit(db.Model):
  __tablename__ = 'community_unit'

  id = Column(String(65), primary_key=True, nullable=False, index=True)
  name = Column(String(45), nullable=False)
  mappingid = Column(ForeignKey(u'mapping.id'), nullable=True, index=True)
  lat = Column(Float, server_default=text("'0'"))
  lon = Column(Float, server_default=text("'0'"))
  country = Column(String(45))
  subcountyid = Column(ForeignKey(u'subcounty.id'), nullable=True, index=True)
  linkfacilityid = Column(ForeignKey(u'link_facility.id'), nullable=True, index=True)
  areachiefname = Column(String(45))
  ward = Column(String(65))
  economicstatus = Column(String(45))
  privatefacilityforact = Column(String(45))
  privatefacilityformrdt = Column(String(45))
  nameofngodoingiccm = Column(String(45))
  nameofngodoingmhealth = Column(Text)
  client_time = Column(Numeric, nullable=True)
  date_added = db.Column(db.DateTime(), default=datetime.utcnow)
  addedby = Column(ForeignKey(u'users.id'), nullable=True, index=True)
  numberofchvs = Column(Integer, server_default=text("'0'"))
  householdperchv = Column(Integer, server_default=text("'0'"))
  numberofvillages = Column(Integer, server_default=text("'0'"))
  distancetobranch = Column(Integer, server_default=text("'0'"))
  transportcost = Column(Integer, server_default=text("'0'"))
  distancetomainroad = Column(Integer, server_default=text("'0'"))
  noofhouseholds = Column(Integer, server_default=text("'0'"))
  mohpoplationdensity = Column(Integer, server_default=text("'0'"))
  estimatedpopulationdensity = Column(Integer, server_default=text("'0'"))
  distancetonearesthealthfacility = Column(Integer, server_default=text("'0'"))
  actlevels = Column(Integer, server_default=text("'0'"))
  actprice = Column(Integer, server_default=text("'0'"))
  mrdtlevels = Column(Integer, server_default=text("'0'"))
  mrdtprice = Column(Integer, server_default=text("'0'"))
  noofdistibutors = Column(Integer, server_default=text("'0'"))
  chvstrained = Column(Integer, server_default=text("'0'"))
  presenceofestates = Column(Integer, server_default=text("'0'"))
  presenceoffactories = Column(Integer, server_default=text("'0'"))
  presenceofhostels = Column(Integer, server_default=text("'0'"))
  tradermarket = Column(Integer, server_default=text("'0'"))
  largesupermarket = Column(Integer, server_default=text("'0'"))
  ngosgivingfreedrugs = Column(Integer, server_default=text("'0'"))
  ngodoingiccm = Column(Integer, server_default=text("'0'"))
  ngodoingmhealth = Column(Integer, server_default=text("'0'"))
  comment = Column(Text)
  archived = Column(Integer, server_default=text("'0'"))
  other = Column(Text, nullable=True, server_default=text("'{}'"))

  mapping = relationship(u'Mapping')
  user = relationship(u'User')
  subcounty = relationship(u'SubCounty')
  linkfacility = relationship(u'LinkFacility')

  @staticmethod
  def from_json(json):
    cu = CommunityUnit()

    for k, v in json.iteritems():
      if k == 'date_added':
        continue
      else:
        if v != '':
          setattr(cu, k, v)
        
    return cu
  
  def to_json(self):
    return {
      'id': self.id,
      'name': self.name if self.name is not None else None,
      'mappingid': self.mappingid if self.mappingid is not None else None,
      'lat': self.lat if self.lat is not None else None,
      'lon': self.lon if self.lon is not None else None,
      'country': self.country if self.country is not None else None,
      'subcountyid': self.subcountyid if self.subcountyid is not None else None,
      'linkfacilityid': self.linkfacilityid if self.linkfacilityid is not None else None,
      'areachiefname': self.areachiefname if self.areachiefname is not None else None,
      'ward': self.ward if self.ward is not None else None,
      'economicstatus': self.economicstatus if self.economicstatus is not None else None,
      'privatefacilityforact': self.privatefacilityforact if self.privatefacilityforact is not None else None,
      'privatefacilityformrdt': self.privatefacilityformrdt if self.privatefacilityformrdt is not None else None,
      'nameofngodoingiccm': self.nameofngodoingiccm if self.nameofngodoingiccm is not None else None,
      'nameofngodoingmhealth': self.nameofngodoingmhealth if self.nameofngodoingmhealth is not None else None,
      'client_time': self.client_time if self.client_time is not None else None,
      'date_added': self.date_added if self.date_added is not None else None,
      'addedby': self.addedby if self.addedby is not None else None,
      'numberofchvs': self.numberofchvs if self.numberofchvs is not None else None,
      'householdperchv': self.householdperchv if self.householdperchv is not None else None,
      'numberofvillages': self.numberofvillages if self.numberofvillages is not None else None,
      'distancetobranch': self.distancetobranch if self.distancetobranch is not None else None,
      'transportcost': self.transportcost if self.transportcost is not None else None,
      'distancetomainroad': self.distancetomainroad if self.distancetomainroad is not None else None,
      'noofhouseholds': self.noofhouseholds if self.noofhouseholds is not None else None,
      'mohpoplationdensity': self.mohpoplationdensity if self.mohpoplationdensity is not None else None,
      'estimatedpopulationdensity': self.estimatedpopulationdensity if self.estimatedpopulationdensity is not None else None,
      'distancetonearesthealthfacility': self.distancetonearesthealthfacility if self.distancetonearesthealthfacility is not None else None,
      'actlevels': self.actlevels if self.actlevels is not None else None,
      'actprice': self.actprice if self.actprice is not None else None,
      'mrdtlevels': self.mrdtlevels if self.mrdtlevels is not None else None,
      'mrdtprice': self.mrdtprice if self.mrdtprice is not None else None,
      'noofdistibutors': self.noofdistibutors if self.noofdistibutors is not None else None,
      'chvstrained': self.chvstrained if self.chvstrained is not None else None,
      'presenceofestates': self.presenceofestates if self.presenceofestates is not None else None,
      'presenceoffactories': self.presenceoffactories if self.presenceoffactories is not None else None,
      'presenceofhostels': self.presenceofhostels if self.presenceofhostels is not None else None,
      'tradermarket': self.tradermarket if self.tradermarket is not None else None,
      'largesupermarket': self.largesupermarket if self.largesupermarket is not None else None,
      'ngosgivingfreedrugs': self.ngosgivingfreedrugs if self.ngosgivingfreedrugs is not None else None,
      'ngodoingiccm': self.ngodoingiccm if self.ngodoingiccm is not None else None,
      'ngodoingmhealth': self.ngodoingmhealth if self.ngodoingmhealth is not None else None,
      'comment': self.comment if self.comment is not None else None,
      'archived': self.archived if self.archived is not None else None,
      'other': self.other
    }

  


class LinkFacility(db.Model):
  __tablename__ = 'link_facility'

  id = Column(String(64), primary_key=True, nullable=False)
  facility_name=Column(String(64))
  county=Column(String(64))
  lat=Column(Float, server_default=text("'0'"))
  lon=Column(Float, server_default=text("'0'"))
  subcounty=Column(String(64))
  client_time = Column(Numeric, nullable=True)
  date_added = db.Column(db.DateTime(), default=datetime.utcnow)
  addedby = Column(ForeignKey(u'users.id'), nullable=True, index=True)
  mrdt_levels=Column(Integer, nullable=False, server_default=text("'0'"))
  act_levels=Column(Integer, nullable=False, server_default=text("'0'"))
  country=Column(String(64))
  facility_id=Column(String(64), nullable=True)
  archived = Column(Integer, nullable=False, server_default=text("'0'"))
  other = Column(Text, nullable=True, server_default=text("'{}'"))
  
  def to_json(self):
    json_record ={
      'id': self.id if self.id is not None else None,
      'facility_name': self.facility_name if self.facility_name else None,
      'county': self.county if self.county else None,
      'lat': float(self.lat) if self.lat else None,
      'lon': float(self.lon) if self.lon else None,
      'subcounty': self.subcounty if self.subcounty else None,
      'client_time': float(self.client_time) if self.client_time else None,
      'date_added': self.date_added if self.date_added else None,
      'addedby': self.addedby if self.addedby else None,
      'mrdt_levels': float(self.mrdt_levels) if self.mrdt_levels else None,
      'act_levels': float(self.act_levels) if self.act_levels else None,
      'country': self.country if self.country else None,
      'mfl_code': self.facility_id if self.facility_id else None,
      'archived': self.archived if self.archived else None,
      'other': self.other
    }
    return json_record
  
  
  @staticmethod
  def from_json(json):
    link_facility = LinkFacility()

    for k, v in json.iteritems():
      if k == 'date_added':
        continue
      
      if k == 'lat' or k == 'lon':
        v = float(v) if bool(v) else float(0)
        
      if k == 'mfl_code':
        k = 'facility_id'
          
      setattr(link_facility, k, v)

    return link_facility
    

  user=relationship(u'User')

class County(db.Model):
  __tablename__ = 'ke_county'

  id = Column(Integer, primary_key=True, nullable=False)
  name = Column(String(65), nullable=False)
  short_code = Column(String(65))
  archived = Column(Integer, server_default=text("'0'"))

  subcounties = relationship(u'SubCounty', back_populates='county', lazy='dynamic')


class SubCounty(db.Model):
  __tablename__ = 'subcounty'

  id = Column(String(64), primary_key=True)
  name = Column(String(64))
  countyID = Column(ForeignKey(u'ke_county.id'), nullable=True, index=True)
  country = Column(String(64))
  mappingId = Column(ForeignKey(u'mapping.id'), nullable=True, index=True)
  lat = Column(Float, server_default=text("'0'"))
  lon = Column(Float, server_default=text("'0'"))
  contactPerson = Column(String(64))
  contactPersonPhone = Column(String(64))
  mainTown = Column(String(64))
  countySupport = Column(String(64))
  subcountySupport = Column(String(64))
  chv_activity_level = Column(String(64))
  countyPopulation = Column(String(64))
  subCountyPopulation = Column(String(64))
  noOfVillages = Column(String(64))
  mainTownPopulation = Column(String(64))
  servicePopulation = Column(String(64))
  populationDensity = Column(String(64))
  transportCost = Column(String(64))
  majorRoads = Column(String(64))
  healtFacilities = Column(String(64))
  privateClinicsInTown = Column(String(64))
  privateClinicsInRadius = Column(String(64))
  communityUnits = Column(String(64))
  mainSupermarkets = Column(String(64))
  mainBanks = Column(String(64))
  anyMajorBusiness = Column(String(64))
  comments = Column(Text)
  recommendation = Column(Integer, server_default=text("'0'"))
  client_time = Column(Numeric, nullable=True)
  date_added = db.Column(db.DateTime(), default=datetime.utcnow)
  addedby = Column(ForeignKey(u'users.id'), nullable=True, index=True)

  user = relationship(u'User')
  mapping = relationship(u'Mapping')
  county = relationship(u'County', back_populates='subcounties')
  wards = relationship(u'Ward', back_populates='subcounty', lazy='dynamic')

  @staticmethod
  def create_subcounties():
    pass

  def to_json(self):
    json_record = {
      'id': self.id,
      'name': self.name,
      'countyID': self.countyID,
      'country': self.country,
      'mappingId': self.mappingId,
      'lat': self.lat,
      'lon': self.lon,
      'contactPerson': self.contactPerson,
      'contactPersonPhone': self.contactPersonPhone,
      'mainTown': self.mainTown,
      'countySupport': self.countySupport,
      'subcountySupport': self.subcountySupport,
      'chv_activity_level': self.chv_activity_level,
      'countyPopulation': self.countyPopulation,
      'subCountyPopulation': self.subCountyPopulation,
      'noOfVillages': self.noOfVillages,
      'mainTownPopulation': self.mainTownPopulation,
      'servicePopulation': self.servicePopulation,
      'populationDensity': self.populationDensity,
      'transportCost': self.transportCost,
      'majorRoads': self.majorRoads,
      'healtFacilities': self.healtFacilities,
      'privateClinicsInTown': self.privateClinicsInTown,
      'privateClinicsInRadius': self.privateClinicsInRadius,
      'communityUnits': self.communityUnits,
      'mainSupermarkets': self.mainSupermarkets,
      'mainBanks': self.mainBanks,
      'anyMajorBusiness': self.anyMajorBusiness,
      'comments': self.comments,
      'recommendation': self.recommendation,
      'client_time': float(self.client_time),
      'date_added': self.date_added,
      'addedby': self.addedby,
      'wards':[ward.to_json() for ward in self.wards]
    }
    return json_record


class Ward(db.Model):
  __tablename__ = 'ward'

  id = Column(String(64), primary_key=True)
  name = Column(String(65), nullable=False)
  sub_county = Column(ForeignKey(u'subcounty.id'), index=True)
  county = Column(Integer)
  archived = Column(Integer, server_default=text("'0'"))

  subcounty = relationship(u'SubCounty', back_populates='wards')

  def to_json(self):
    json_record={
      'id':self.id,
      'name':self.name,
      'sub_county':self.sub_county,
      'county':self.county,
      'archived':self.archived
    }
    return json_record

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
                loc = Location(name=name.get('name'), country='UG', lat=name.get('lat'), lon=name.get('lon'),
                               admin_name='Country')
            db.session.add(loc)
        db.session.commit()

        # create locations based on the template given
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
                    s_county = Location(name=sub_county.get('name').title(), admin_name='Sub-County', country='UG',
                                        parent=county.id, code=sub_county.get('number'))
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

    tasks = db.relationship('Task', backref='user', lazy='dynamic')

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
    
    def to_json(self):
        json_record={
            'id':self.id,
            'email':self.email,
            'username':self.username,
            'role_id':self.role_id,
            'confirmed':self.confirmed,
            'name':self.name,
            'location':self.location,
            'about_me':self.about_me,
            'member_since':self.member_since,
            'last_seen':self.last_seen,
            'geo_id':self.geo_id,
            'user_type_id':self.user_type_id,
        }
        return json_record

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def generate_auth_token(self, expiration = 3600):
        """
        Generates an auth_token to be used for authenticated HTTP requests
        :param expiration: Expiration time in Seconds. Default = 3600
        :return:
        """
        s = Serializer(current_app.config['SECRET_KEY'], expires_in = expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        """
        A static method to verify if an authentication token is legit.
        :param token: auth_token to verify
        :return:
        """
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        user = User.query.get(data['id'])
        return user

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
        self.app_name = new_password.encode('base64')
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

    def __str__(self):
      return '%s (%s)' % (self.username, self.name)


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
    
    
class Training(db.Model):
  __tablename__ = 'training'

  id = db.Column(db.String(64), primary_key=True, nullable=False)
  training_name = db.Column(db.String(64), nullable=False)
  country = Column(String(64))
  county_id = Column(ForeignKey(u'ke_county.id'), nullable=True, index=True)
  location_id = Column(ForeignKey(u'location.id'), nullable=True, index=True)
  subcounty_id = Column(ForeignKey(u'subcounty.id'), nullable=True, index=True)
  ward_id = Column(ForeignKey(u'ward.id'), nullable=True, index=True)
  district = db.Column(db.String(45), nullable=True)
  recruitment_id = Column(ForeignKey(u'recruitments.id'), nullable=True, index=True)
  parish_id = Column(ForeignKey(u'parish.id'), nullable=True, index=True)
  lat = Column(Float, server_default=text("'0'"))
  lon = Column(Float, server_default=text("'0'"))
  training_venue_id = Column(ForeignKey(u'training_venues.id'), nullable=True, index=True)
  training_status_id = Column(ForeignKey(u'training_status.id'), nullable=True, index=True)
  client_time = db.Column(db.Numeric)
  created_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
  date_created = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)
  archived = Column(Integer, server_default=text("'0'"))
  comment = Column(Text, nullable=True)
  date_commenced = db.Column(Numeric, nullable=True)
  date_completed = db.Column(Numeric, nullable=True)

  county = relationship(u'County')
  location = relationship(u'Location')
  subcounty = relationship(u'SubCounty')
  ward = relationship(u'Ward')
  parish = relationship(u'Parish')
  user = relationship(u'User')
  #recruitment = relationship(u'Recruitments')
  training_venue = relationship(u'TrainingVenues')
  
  def to_json(self):
    json_record = {
      'id':self.id,
      'training_name':self.training_name,
      'country':self.country,
      'county_id':self.county_id,
      'location_id':self.location_id,
      'subcounty_id':self.subcounty_id,
      'ward_id':self.ward_id,
      'district':self.district,
      'recruitment_id':self.recruitment_id,
      'parish_id':self.parish_id,
      'lat':self.lat,
      'lon':self.lon,
      'training_status_id':self.training_status_id,
      'client_time':float(self.client_time),
      'created_by':self.created_by,
      'date_created':self.date_created,
      'archived':self.archived,
      'comment':self.comment,
      'date_commenced':self.date_commenced,
      'date_completed':self.date_completed,
      'training_venue_id' : self.training_venue_id,
      'training_venue_details': self.training_venue.to_json() if self.training_venue else None
    }
    return json_record
    
  @staticmethod
  def from_json(json):
    return Training(
        id = json.get('id'),
        training_name = json.get('training_name'),
        country = json.get('country'),
        county_id = json.get('county_id'),
        location_id = json.get('location_id'),
        subcounty_id = json.get('subcounty_id'),
        ward_id = json.get('ward_id'),
        district = json.get('district'),
        recruitment_id = json.get('recruitment_id'),
        parish_id = json.get('parish_id'),
        lat = json.get('lat'),
        lon = json.get('lon'),
        status = json.get('status'),
        client_time = json.get('client_time'),
        created_by = json.get('created_by'),
        date_created = json.get('date_created'),
        archived = json.get('archived'),
        comment = json.get('comment'),
    )
  
  def commences(self):
    if self.date_completed is not None:
      return time.strftime('%d %b, %Y', time.localtime(self.date_commenced / 1000))
    else:
      return None
  
  def completes (self):
    if self.date_completed is not None:
      return time.strftime('%d %b, %Y', time.localtime(self.date_completed / 1000))
    else:
      return None


class TrainingVenues(db.Model):
  __tablename__ = 'training_venues'

  id = Column(String(64), primary_key=True, nullable=False)
  name = Column(String(64), nullable=True)
  mapping = Column(ForeignKey(u'mapping.id'), nullable=True)
  lat = Column(Float, server_default=text('0'), nullable=False)
  lon = Column(Float, server_default=text('0'), nullable=False)
  inspected = Column(Integer, server_default=text("'0'"))
  country = Column(String(20))
  selected = Column(Integer, server_default=text("'0'"))
  capacity = Column(Integer, server_default=text("'0'"))
  date_added = Column(db.DateTime(), default=datetime.utcnow, nullable=False)
  added_by = Column(Integer, nullable=True)
  client_time = Column(Numeric, nullable=True)
  meta_data = Column(Text, nullable=True)
  archived = Column(Integer, server_default=text("'0'"))
  
  def to_json(self):
      return {}


class SessionAttendance(db.Model):
  __tablename__ = 'session_attendance'
  
  id = Column(String(64), primary_key=True, nullable=False)
  training_session_id = Column(ForeignKey(u'training_session.id'), nullable=True, index=True)
  trainee_id = Column(ForeignKey(u'registrations.id'), nullable=True, index=True)
  training_session_type_id = Column(ForeignKey(u'training_session_type.id'), nullable=True, index=True)
  training_id = Column(ForeignKey(u'training.id'), nullable=True, index=True)
  country = db.Column(db.String(20), nullable=False)
  attended = Column(Integer, server_default=text("'0'"))
  client_time = db.Column(db.Numeric)
  created_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
  date_created = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)
  archived = Column(Integer, server_default=text("'0'"))
  comment = Column(Text, nullable=True)
  
  training_session = relationship(u'TrainingSession')
  trainee = relationship(u'Registration')
  training_session_type = relationship(u'TrainingSessionType')
  training = relationship(u'Training')
  user = relationship(u'User')
  
  def to_json(self):
    return {
      'id': self.id,
      'training_session_id': self.training_session_id,
      'trainee_id': self.trainee_id,
      'training_session_type_id': self.training_session_type_id,
      'training_id': self.training_id,
      'country': self.country,
      'attended': self.attended,
      'client_time': float(self.client_time) if self.client_time is not None else None,
      'created_by': self.created_by,
      'date_created': self.date_created,
      'archived': self.archived,
      'comment': self.comment
    }

  @staticmethod
  def from_json(json_record):
    return SessionAttendance(
        id=json_record.get('id') if json_record.get('id') is not None else None,
        training_session_id=json_record.get('training_session_id') if json_record.get(
          'training_session_id') is not None else None,
        trainee_id=json_record.get('trainee_id') if json_record.get('trainee_id') is not None else None,
        training_session_type_id=json_record.get('training_session_type_id') if json_record.get(
          'training_session_type_id') is not None else None,
        training_id=json_record.get('training_id') if json_record.get('training_id') is not None else None,
        country=json_record.get('country') if json_record.get('country') is not None else None,
        attended=json_record.get('attended') if json_record.get('attended') is not None else None,
        client_time=json_record.get('client_time') if json_record.get('client_time') is not None else None,
        created_by=json_record.get('created_by') if json_record.get('created_by') is not None else None,
        date_created=json_record.get('date_created') if json_record.get('date_created') is not None else None,
        archived=json_record.get('archived') if json_record.get('archived') is not None else None,
        comment=json_record.get('comment') if json_record.get('comment') is not None else None
    )

class SessionTopic(db.Model):
  __tablename__ = 'session_topic'

  id = Column(Integer, primary_key=True, nullable=False)
  name = Column(String(70), nullable=False)
  country = Column(String(20))
  archived = Column(Integer, server_default=text("'0'"))
  date_added = Column(DateTime(), default=datetime.utcnow, nullable=False)
  added_by = Column(ForeignKey(u'users.id'), nullable=False, index=True)

  user = relationship(u'User')
  
  def to_json(self):
    return {
      'id':self.id,
      'name':self.name,
      'country':self.country,
      'archived':self.archived,
      'date_added':self.date_added,
      'added_by':self.added_by
    }


class TrainingSession(db.Model):
  __tablename__ = 'training_session'

  id = db.Column(db.String(64), primary_key=True, nullable=False, unique=True)
  training_session_type_id = Column(ForeignKey(u'training_session_type.id'), nullable=True, index=True)
  class_id = Column(ForeignKey(u'training_classes.id'), nullable=True, index=False)
  training_id = Column(ForeignKey(u'training.id'), nullable=False, index=True)
  trainer_id = Column(ForeignKey(u'users.id'), nullable=True, index=True)
  country = db.Column(db.String(20))
  archived = Column(Integer, server_default=text("'0'"))
  comment = Column(Text, nullable=True)
  session_start_time = db.Column(db.Numeric)
  session_end_time = db.Column(db.Numeric)
  session_topic_id = Column(ForeignKey(u'session_topic.id'), nullable=True, index=True)
  session_lead_trainer = Column(ForeignKey(u'users.id'), nullable=True, index=True)
  client_time = db.Column(db.Numeric)
  created_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
  date_created = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)

  training_session_type = relationship(u'TrainingSessionType')
  session_class = relationship(u'TrainingClasses')
  training = relationship(u'Training')
  lead_trainer = relationship(u'User', foreign_keys=[session_lead_trainer])
  trainer = relationship(u'User', foreign_keys=[trainer_id])
  session_creator = relationship(u'User', foreign_keys=[created_by])
  session_topic = relationship(u'SessionTopic')
  
  def to_json(self):
    return {
      'id':self.id,
    'training_session_type_id':self.training_session_type_id,
    'class_id':self.class_id,
    'training_id':self.training_id,
    'trainer_id':self.trainer_id,
    'country':self.country,
    'archived':self.archived,
    'comment':self.comment,
    'session_start_time':float(self.session_start_time) if self.session_start_time is not None else None,
    'session_end_time':float(self.session_end_time) if self.session_end_time is not None else None,
    'session_topic_id':self.session_topic_id,
    'session_lead_trainer':self.session_lead_trainer,
    'client_time': float(self.client_time) if self.client_time is not None else None,
    'created_by':self.created_by,
    'date_created': self.date_created,
    }


class TrainingSessionType(db.Model):
  __tablename__ = 'training_session_type'

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  session_name = db.Column(db.String(20))
  country = db.Column(db.String(20), nullable=False)
  archived = Column(Integer, server_default=text("'0'"))
  client_time = db.Column(db.Numeric)
  created_by = Column(ForeignKey(u'users.id'), nullable=False, index=True)
  date_created = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)

  user = relationship(u'User')
    

class TrainingStatus(db.Model):
  __tablename__ = 'training_status'

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  name = db.Column(db.String(20))
  archived = Column(Integer, server_default=text("'0'"))
  readonly = Column(Integer, server_default=text("'0'"))
  country = db.Column(db.String(20), nullable=False)
  client_time = db.Column(db.Numeric)
  created_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
  date_created = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)

  user = relationship(u'User')
  
  def to_json(self):
    return{
      'id': self.id if self.id is not None else None,
      'name': self.name if self.name is not None else None,
      'archived': self.archived==1 if self.archived is not None else None,
      'readonly': self.readonly==1 if self.readonly is not None else None,
      'country': self.country if self.country is not None else None,
      'client_time': self.client_time if self.client_time is not None else None,
      'created_by': self.created_by if self.created_by is not None else None,
      'date_created': self.date_created if self.date_created is not None else None
    }
  
  
class TraineeStatus(db.Model):
  __tablename__ = 'trainee_status'

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  name = db.Column(db.String(20))
  archived = Column(Integer, server_default=text("'0'"))
  readonly = Column(Integer, server_default=text("'0'"))
  country = db.Column(db.String(20), nullable=False)
  client_time = db.Column(db.Numeric)
  created_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
  date_created = db.Column(db.DateTime(), default=datetime.utcnow, nullable=True)

  user = relationship(u'User')
  
  def to_json(self):
    return {
      'id': self.id if self.id is not None else None,
      'name': self.name if self.name is not None else None,
      'archived': self.archived==1 if self.archived is not None else None,
      'readonly': self.readonly if self.readonly is not None else None,
      'country': self.country if self.country is not None else None,
      'client_time': self.client_time if self.client_time is not None else None,
      'created_by': self.created_by if self.created_by is not None else None,
      'date_created': self.date_created if self.date_created is not None else None
    }


class TrainingRoles(db.Model):
  __tablename__ = 'training_roles'
  
  id = db.Column(db.Integer, primary_key=True, nullable=False)
  role_name = db.Column(db.String(20))
  archived = Column(Integer, server_default=text("'0'"))
  readonly = Column(Integer, server_default=text("'0'"))
  country = db.Column(db.String(20), nullable=False)
  client_time = db.Column(db.Numeric)
  created_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
  date_created = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)

  user = relationship(u'User')
  
  
  def _asdict(self):
    return asdict(self)
    

class TrainingTrainers(db.Model):
  __tablename__ = 'training_trainers'

  id = Column(Integer, primary_key=True, nullable=False)
  training_id = Column(ForeignKey(u'training.id'), nullable=True, index=True)
  class_id = Column(ForeignKey(u'training_classes.id'), nullable=True, index=True)
  trainer_id = Column(ForeignKey(u'users.id'), nullable=True, index=True)
  country = Column(String(20))
  client_time = db.Column(db.Numeric)
  created_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
  date_created = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)
  archived = Column(Integer, server_default=text("'0'"))
  training_role_id = Column(ForeignKey(u'training_roles.id'), nullable=True, index=True)

  trainer = relationship(u'User', foreign_keys=[trainer_id])
  user = relationship(u'User', foreign_keys=[created_by])
  training_role = relationship(u'TrainingRoles')

  def _asdict(self):
    trainer =  asdict(self)
    trainer['trainer'] = self.trainer.to_json()
    trainer['role'] = self.training_role._asdict() if self.training_role is not None else None
    return trainer
    

class TrainingClasses(db.Model):
  __tablename__ = 'training_classes'

  id = Column(Integer, primary_key=True, nullable=False)
  training_id = Column(ForeignKey(u'training.id'), nullable=False, index=True)
  class_name = Column(String(20), nullable=False)
  created_by = Column(ForeignKey(u'users.id'), nullable=False, index=True)
  client_time = Column(db.Numeric)
  date_created = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)
  archived = Column(Integer, server_default=text("'0'"))
  country = Column(String(20), server_default=text("'UG'"), nullable=False)
  lead_trainer = Column(ForeignKey(u'users.id'), nullable=True, index=False)

  class_creator = relationship(u'User', foreign_keys=[created_by])
  training = relationship(u'Training')
  trainer = relationship(u'User', foreign_keys=[lead_trainer])

  def to_json(self):
    json_record = {
      'id': self.id,
      'class_name': self.class_name,
      'created_by': self.created_by,
      'client_time': float(self.client_time),
      'training_id': self.training_id,
      'date_created': self.date_created,
      'archived': self.archived,
      'country': self.country,
      'lead_trainer': self.lead_trainer
    }
    return json_record

  @staticmethod
  def from_json(json_record):
    return TrainingClasses(
      id=json_record.get('id'),
      class_name=json_record.get('class_name'),
      created_by=json_record.get('created_by'),
      client_time=json_record.get('client_time'),
      date_created=json_record.get('date_created')
    )


class Trainees(db.Model):
  __tablename__ = 'trainees'

  id = Column(String(64), primary_key=True, nullable=False)
  registration_id = Column(ForeignKey(u'registrations.id'), nullable=False, index=True)
  class_id = Column(ForeignKey(u'training_classes.id'), nullable=False, index=True)
  training_id = Column(ForeignKey(u'training.id'), nullable=False, index=True)
  country = Column(String(20), server_default=text("'UG'"), nullable=False)
  date_created = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)
  added_by = Column(ForeignKey(u'users.id'), nullable=False, index=True)
  client_time = Column(db.Numeric)
  branch = Column(ForeignKey(u'branch.id'), nullable=True, index=True)
  cohort = Column(ForeignKey(u'cohort.id'), nullable=True, index=True)
  chp_code = Column(String(45), nullable=True)
  comment = Column(Text, nullable=True)
  trainee_status = Column(ForeignKey(u'trainee_status.id'), nullable=True)
  
  registration = relationship(u'Registration')

  def to_json(self):
    json_record = {
      'id': self.id,
      'registration_id': self.registration_id,
      'registration': self.registration.to_json(),
      'class_id': self.class_id,
      'training_id': self.training_id,
      'country': self.country,
      'date_created': self.date_created,
      'added_by': self.added_by,
      'client_time': float(self.client_time),
      'branch': self.branch,
      'cohort': self.cohort,
      'chp_code': self.chp_code,
      'comment': self.comment,
    }
    return json_record

  @staticmethod
  def from_json(json_record):
    return Trainees(
      id=json_record.get('id'),
      registration_id=json_record.get('id'),
      class_id=json_record.get('class_id'),
      training_id=json_record.get('training_id')
    )


class CertificationType(db.Model):
    __tablename__ = 'certification_types'
  
    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    proportion = Column(Float, nullable=False, server_default=text("'0'"))
    archived = Column(db.Boolean, default=False)
    country = Column(String(20), server_default=text("'UG'"), nullable=False)
    
    def to_json(self):
        return asdict(self)


class ExamTraining(db.Model):
    __tablename__ = 'exam_trainings'

    id = Column(Integer, primary_key=True)
    title = Column(String(45))
    created_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
    date_created = Column(db.DateTime(), default=datetime.utcnow, nullable=False)
    passmark = Column(Integer, nullable=True)
    exam_status_id = Column(ForeignKey(u'exam_status.id'), nullable = True, index = True)
    certification_type_id = Column(ForeignKey(u'certification_types.id'), nullable=True, index=True)
    archived = Column(db.Boolean, default=False)
    country = Column(String(20), server_default=text("'UG'"), nullable=False)
    
    exam_status = relationship(u'ExamStatus')
    certification_type = relationship(u'CertificationType')

    def _asdict(self):
        return asdict(self)
    

    def to_json(self):
        return self._asdict()
    
    def is_certification(self):
      return bool(self.certification_type_id)
    

class ExamQuestion(db.Model):
    __tablename__ = 'exam_questions'

    id = Column(Integer, primary_key=True, unique=True)
    exam_id = Column(ForeignKey(u'exam_trainings.id'), index=True)
    question_id = Column(ForeignKey(u'questions.id'), index=True)
    weight = Column(Integer)
    allocated_marks = Column(Integer)
    created_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
    date_created = Column(db.DateTime(), default=datetime.utcnow, nullable=False)
    country = Column(String(20), server_default=text("'UG'"), nullable=False)
    archived = Column(db.Boolean, default=False)

    exam = relationship(u'ExamTraining')
    question = relationship(u'Question')
    
    
    def _asdict(self):
      result = OrderedDict()
      for key in self.__mapper__.c.keys():
        result[key] = getattr(self, key)
      return result


class ExamResult(db.Model):
    __tablename__ = 'exam_results'

    id = Column(String(64), primary_key=True, nullable=False, index=True)
    training_exam_id = Column(ForeignKey(u'training_exams.id'), index=True)
    trainee_id = Column(ForeignKey(u'registrations.id'), nullable=False, index=True)
    question_id = Column(ForeignKey(u'questions.id'), index=True)
    question_score = Column(Numeric(8, 2))
    created_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
    date_created = Column(db.DateTime(), default=datetime.utcnow, nullable=False)
    archived = Column(db.Boolean, default=False)
    country = Column(String(20), server_default=text("'UG'"), nullable=False)
    answer = Column(String(256), nullable=True)
    choice_id = Column(Integer, nullable=True)
    
    question = relationship(u'Question')
    training_exam = relationship(u'TrainingExam')
    
    @staticmethod
    def from_json(json_record):
      exam_result =  ExamResult(
        id=json_record.get("id", None),
        training_exam_id=json_record.get("training_exam_id"),
        trainee_id=json_record.get("trainee_id"),
        question_id=json_record.get("question_id"),
        question_score=json_record.get("question_score"),
        country=json_record.get("country"),
        answer=json_record.get("answer"),
        choice_id=json_record.get("choice_id")
      )
      
      if exam_result.id is None:
        exam_result.id = str(uuid.uuid4())
        
      return exam_result

class ExamStatus(db.Model):
    __tablename__ = 'exam_status'

    id = Column(Integer, primary_key=True)
    title = Column(String(45))
    created_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
    date_created = Column(db.DateTime(), default=datetime.utcnow, nullable=False)
    archived = Column(db.Boolean, default=False)
    country = Column(String(20), server_default=text("'UG'"), nullable=False)
    
    def _asdict(self):
      result = OrderedDict()
      for key in self.__mapper__.c.keys():
        result[key] = getattr(self, key)
      return result
    
    def as_json(self):
      return self._asdict()
    

class Question(db.Model):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)
    allocated_marks = Column(Numeric(8,2))
    question_type_id = Column(ForeignKey(u'question_types.id'), nullable=True, index=True)
    created_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
    date_created = Column(db.DateTime(), default=datetime.utcnow, nullable=False)
    archived = Column(db.Boolean, default=False)
    batch_id = Column(String(64), nullable=True)
    choices = relationship(u'QuestionChoice', back_populates='question', lazy='dynamic')
    country = Column(String(20), server_default=text("'KE'"), nullable=False)

    question_type = relationship(u'QuestionType')

    def to_json(self):
        return self._asdict()

    def _asdict(self):
        result = OrderedDict()
        for key in self.__mapper__.c.keys():
            result[key] = getattr(self, key)
        result['choices'] = [choice.to_json() for choice in self.choices]
        result['type'] = self.question_type.to_json() if self.question_type is not None else None
        result['topics'] = [t.session_topic.to_json() for t in QuestionTopic.query.filter_by(question_id=self.id, archived=False)]
        return result


class QuestionChoice(db.Model):
    __tablename__ = 'question_choices'

    id = Column(Integer, primary_key=True)
    question_id = Column(ForeignKey(u'questions.id'), nullable=False, index=False)
    question_choice = Column(String(256))
    is_answer = Column(db.Boolean, default=False)
    allocated_marks = Column(Numeric(8,2), nullable=True)
    created_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
    date_created = Column(db.DateTime(), default=datetime.utcnow, nullable=False)
    archived = Column(db.Boolean, default=False)
    question = relationship(u'Question', back_populates='choices')
    country = Column(String(20), server_default=text("'KE'"), nullable=False)
    
    def to_json(self):
      return self._asdict()

    def _asdict(self):
      result = OrderedDict()
      for key in self.__mapper__.c.keys():
        result[key] = getattr(self, key)
      return result

class QuestionTopic(db.Model):
    __tablename__ = 'question_topics'

    id = Column(Integer, primary_key=True)
    question_id = Column(ForeignKey(u'questions.id'), index=True)
    session_topic_id = Column(ForeignKey(u'session_topic.id'), nullable=True, index=True)
    created_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
    date_created = Column(db.DateTime(), default=datetime.utcnow, nullable=False)
    archived = Column(db.Boolean, default=False)
    country = Column(String(20), server_default=text("'KE'"), nullable=False)

    question = relationship(u'Question')
    session_topic = relationship(u'SessionTopic')


class QuestionType(db.Model):
    __tablename__ = 'question_types'

    id = Column(Integer, primary_key=True)
    display_title = Column(String(45))
    widget_type = Column(String(64))
    created_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
    date_created = Column(db.DateTime(), default=datetime.utcnow, nullable=False)
    archived = Column(db.Boolean, default=False)

    def to_json(self):
        return self._asdict()

    def _asdict(self):
      result = OrderedDict()
      for key in self.__mapper__.c.keys():
        result[key] = getattr(self, key)
      return result


class TrainingExam(db.Model):
    __tablename__ = 'training_exams'

    id = Column(Integer, primary_key=True)
    training_id = Column(ForeignKey(u'training.id'), nullable=False, index=True)
    exam_id = Column(ForeignKey(u'exam_trainings.id'), index=True)
    date_administered = Column(db.DateTime(), default=datetime.utcnow, nullable=True)
    created_by = Column(ForeignKey(u'users.id'), nullable=True, index=True)
    date_created = Column(db.DateTime(), default=datetime.utcnow, nullable=False)
    archived = Column(db.Boolean, default=False)
    country = Column(String(20), server_default=text("'KE'"), nullable=False)
    passmark = Column(Integer, nullable=True)
    unlock_code = Column(Integer, nullable=True)

    exam = relationship(u'ExamTraining')
    training = relationship(u'Training')
    
    def _asdict(self):
      result = OrderedDict()
      for key in self.__mapper__.c.keys():
        result[key] = getattr(self, key)
        result['title'] = self.exam._asdict().get('title')
        if self.passmark is None:
          result['passmark'] = self.exam.passmark
        
      return result
    

class ErrorLog(db.Model):
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True)
    error = Column(Text, nullable=False)
    endpoint = Column(Text, nullable=False)
    payload = Column(Text, nullable=True)
    datetime = Column(db.DateTime(), default=datetime.utcnow(), nullable=False)
    user = Column(ForeignKey(u'users.id'), nullable=True)
    resolved = Column(db.Boolean, default=False, nullable=False)
    http_method = Column(String(16), nullable=False)
    http_headers = Column(Text, nullable=True)
    http_response_status_code = Column(Integer)
    

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128), nullable=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=True)
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100