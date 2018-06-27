import os

from flask_httpauth import HTTPBasicAuth

from . import api
from flask_login import login_required, current_user, login_user, abort
from flask import Response, request, jsonify
import json
import time
from sqlalchemy import func, distinct, select, exists, and_
from .. import db
from ..models import *
from .. data import data
import csv
import uuid
from ..decorators import api_login_required
from ..utils.utils import *
from ..commons import exam_with_questions_to_dict



@api.after_request
def apply_caching(response):
    response.headers["Content-type"] = "application/json"
    return response

@api.route('/users/login', methods=['POST'])
def users_login():
    """
    API Endpoint to login user and return their details and authentication token
    :return:
    """
    form = request.form
    email = form.get('email', None)
    password = form.get('password', None)

    if not email or not password:
        return jsonify(error='Invalid request'), 400

    user = User.query.filter_by(email=email).first()

    if user is None or not user.verify_password(password):
        return jsonify(error="Invalid login credentials"), 400
    login_user(user)
    return jsonify(user=user.to_json(), auth_token={"token": user.generate_auth_token(), "expires_in": 3600}), 200


@api.route('/recruitments.json')
@api.route('/recruitments.json')
def recruitments_json():
  if request.method == 'GET':
    records = Recruitments.query.filter(Recruitments.archived != 1)
    return jsonify({'recruitments': [record.to_json() for record in records]})
  else:
    recruitments = Recruitments(name=request.form.get('name'))
    db.session.add(recruitments)
    db.session.commit()
    return jsonify(status='ok')


@api.route('/syncke-counties')
@api.route('/sync/ke-counties')
def get_ke_counties_json():
  if request.method == 'GET':
    records = County.query.all()
    return jsonify({'counties': [{'name':record.name, 'code':record.id,
                                  'subcounties':[subcounty.to_json() for subcounty in record.subcounties]}
                                 for record in records]})
  else:
    return jsonify(message='not permitted'), 200
    # return jsonify({"success": True}), 202


@api.route('/recruitment/<string:id>', methods=['GET', 'POST'])
@api_login_required
def api_recruitment(id):
    """
    GET:
    Gets recruitment details for a particular `id`

    POST:
    Updates recruitment details for a particular `id`

    :param id:
    :return:
    """
    if request.method == 'GET':
        page = {'title': 'Recruitments', 'subtitle': 'Recruitments done so far'}
        recruitment = Recruitments.query.filter_by(id=id).first()
        return jsonify({'name': recruitment.name, 'id': recruitment.id})
    else:
        if request.form.get('action') == 'confirmed' or request.form.get('action') == 'draft':
            recruitment = Recruitments.query.filter_by(id=request.form.get('id')).first()
            recruitment.status = request.form.get('action')
            db.session.add(recruitment)
            db.session.commit()
            # also create a draft training, that needs to be confirmed by the Training Team.
            # When training has been confirmed, the person who confirmeed it becomes the owner
            if request.form.get('action') == 'confirmed':
                existing_training = Training.query.filter_by(recruitment_id=recruitment.id).first()
                if not existing_training:
                    training = Training(
                        id=str(uuid.uuid4()),
                        training_name=recruitment.name,
                        country=recruitment.country,
                        district=recruitment.district,
                        recruitment_id=recruitment.id,
                        status=1,
                        client_time=time.time(),
                        created_by=1,
                    )
                    if recruitment.country == 'KE':
                        if recruitment.subcounty_id is not None:
                            training.subcounty_id = recruitment.subcounty_id
                        if recruitment.county_id is not None:
                            training.county_id = recruitment.county_id
                    else:
                        if recruitment.location_id is not None:
                            training.location_id = recruitment.location_id
                    db.session.add(training)
                    db.session.commit()
            return jsonify(status='updated', id=recruitment.id)
        else:
            # recruitments = Recruitments(name=request.form.get('name'))
            # db.session.add(recruitments)
            # db.session.commit()
            return jsonify(status='ok')
    
@api.route('/recruitment_training', methods=['GET','POST'])
@api_login_required
def api_recrutiment_trainig():
  if request.form.get('action') == 'confirmed' or request.form.get('action') == 'draft':
    recruitment = Recruitments.query.filter_by(id=request.form.get('id')).first()
    recruitment.status = request.form.get('action')
    db.session.add(recruitment)
    db.session.commit()
    # also create a draft training, that needs to be confirmed by the Training Team.
    # When training has been confirmed, the person who confirmed it becomes the owner
    if request.form.get('action') == 'confirmed':
      training = create_training(recruitment.id)
      create_training_topics(training)
      
      class_list = generate_training_classes(recruitment.to_json())
      # create a class list
      class_details = class_list.get('details')
      for k, v in class_details.iteritems():
        # class is k, trainees = v
        new_class = TrainingClasses.query.filter_by(training_id=str(training.id),class_name=str(k)).first()
        if not new_class:
          new_class = TrainingClasses(
              training_id = training.id,
              class_name = k,
              created_by=1,
              client_time=int(time.time()),
              date_created=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
              country =recruitment.country
          )
          db.session.add(new_class)
          db.session.commit()
        #   Create trainees
        for trainee_id in v:
          trainee = Trainees.query.filter_by(id=trainee_id).first()
          if not trainee:
            trainee = Trainees(
                id=trainee_id,
                registration_id = trainee_id,
                class_id = new_class.id,
                training_id = training.id,
                country = recruitment.country,
                date_created = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                added_by = 1,
                client_time = int(time.time()),
            )
            db.session.add(trainee)
            db.session.commit()
          #Add the trainee to some sessions
          training_sessions_list = TrainingSession.query.filter_by(training_id=training.id, archived=0)
          for session in training_sessions_list:
            sess = SessionAttendance.query.filter_by(trainee_id=trainee_id, training_session_id=session.id, training_id=training.id).first()
            if not sess:
              sess = SessionAttendance(
                  id = str(uuid.uuid4())
              )
            sess.training_session_id = session.id
            sess.trainee_id = trainee.id
            sess.training_id = training.id
            sess.country = training.country
            sess.client_time = int(time.time())
            sess.date_created = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            db.session.add(sess)
            db.session.commit()
            
      # create / generate Sessions
      #TrainingSessiions, needs to have a training_topic
      # @TODO  create initial 3 training_sessions
        
      #   Create default Trainee attendances here, we export this to the App
      
      return jsonify(status='updated', id=recruitment.id, trainees_classes=class_details)
    #   create classes
    return jsonify(status='updated', id=recruitment.id)
  else:
    return jsonify(status='ok')


@api.route('/get/session-topics', methods=['GET'])
@api_login_required
def get_session_topics():
    return jsonify(topics=[t.to_json() for t in SessionTopic.query.filter_by(archived=0)])


@api.route('/get/training/<string:id>', methods=['GET'])
@api_login_required
def get_training(id):
  training = Training.query.filter_by(id=id).first()
  training = training.to_json()
  training['trainees'] = [record.to_json() for record in Trainees.query.filter_by(training_id=id)]
  training['training_sessions'] = [session.to_json() for session in TrainingSession.query.filter_by(training_id=id)]
  training['classes'] = [record.to_json() for record in TrainingClasses.query.filter_by(training_id=id)]
  training['exams'] = [e._asdict() for e in TrainingExam.query.filter_by(training_id=id, archived=False)]
  training['trainers'] = [t._asdict() for t in
                               TrainingTrainers.query.filter_by(training_id=id, archived=0)]
  return jsonify(training=training)


@api.route('/get/training/session-attendances/<string:id>')
@api_login_required
def get_training_attendance(id):
  return jsonify(attendance =[a.to_json() for a in SessionAttendance.query.filter_by(training_id=id)])


@api.route('/users/json', methods=['GET'])
@api_login_required
def api_users():
  users = User.query.all()
  api_data = []
  for user in users:
    api_data.append({'id':user.id, 'name':user.name, 'country':user.location, 'username': user.username, 'app_name': user.app_name, 'email': user.email})
  return jsonify(users=api_data)


@api.route('/syncrecruitments', methods=['GET', 'POST'])
@api.route('/sync/recruitments', methods=['GET', 'POST'])
@api_login_required
def sync_recruitments():
  if request.method == 'GET':
    records  = Recruitments.query.order_by(Recruitments.client_time.asc()).filter(Recruitments.archived != 1)
    return jsonify({'recruitments':[record.to_json() for record in records]})
  else:
    status = []
    recruitment_list = request.json.get('recruitments')
    if recruitment_list is not None:
      for recruitment in recruitment_list:
        operation=''
        record = Recruitments.from_json(recruitment)
        saved_record  = Recruitments.query.filter(Recruitments.id == record.id).first()
        if saved_record:
          saved_record.id = recruitment.get('id')
          saved_record.name = recruitment.get('name')
          saved_record.lat = recruitment.get('lat')
          saved_record.lon = recruitment.get('lon')
          saved_record.subcounty = recruitment.get('subcounty')
          saved_record.district = recruitment.get('district')
          saved_record.country = recruitment.get('country')
          saved_record.county = recruitment.get('county')
          saved_record.division = recruitment.get('division')
          saved_record.added_by = recruitment.get('added_by')
          saved_record.comment = recruitment.get('comment')
          saved_record.client_time =recruitment.get('client_time')
          saved_record.synced = recruitment.get('synced')
          saved_record.archived = 0
          db.session.add(saved_record)
          db.session.commit()
          operation='updated'
        else:
          db.session.add(record)
          db.session.commit()
          operation='created'
        status.append({'id':record.id, 'status':'ok', 'operation': operation})
      return jsonify(status=status)
    else:
      return jsonify(error="No records posted")

@api.route('/syncregistrations', methods=['GET', 'POST'])
@api.route('/sync/registrations', methods=['GET', 'POST'])
@api_login_required
def sync_registrations():
  if request.method == 'GET':
    records  = Registration.query.filter(Registration.archived != 1)
    return jsonify({'registrations':[record.to_json() for record in records]})
  else:
    status = []
    registration_list = request.json.get('registrations')
    if registration_list is not None:
      for registration in registration_list:
        operation='' #to hold the operation performed so that we can inform the client
        record = Registration.from_json(registration)
        saved_record  = Registration.query.filter(Registration.id == record.id).first()
        if saved_record:
          saved_record.id=registration.get('id') if registration.get('id') != '' \
                                                    or registration.get('id') is not None else None
          saved_record.name =registration.get('name') if registration.get('name') != '' \
                                                         or registration.get('name') is not None else None
          saved_record.phone =registration.get('phone') if registration.get('phone') != '' \
                                                           or registration.get('phone') is not None else None
          saved_record.gender =registration.get('gender') if registration.get('gender') != '' \
                                                             or registration.get('gender') is not None else None
          saved_record.recruitment =registration.get('recruitment') if registration.get('recruitment') != '' \
                                                                       or registration.get('recruitment') is not None else None
          saved_record.country =registration.get('country') if registration.get('country') != '' \
                                                               or registration.get('country') is not None else None
          saved_record.dob =registration.get('dob') if registration.get('dob') != '' \
                                                       or registration.get('dob') is not None else None
          saved_record.district =registration.get('district') if registration.get('district') != '' \
                                                                 or registration.get('district') is not None else None
          saved_record.subcounty =registration.get('subcounty') if registration.get('subcounty') != '' \
                                                                   or registration.get('subcounty') is not None else None
          saved_record.division =registration.get('division') if registration.get('division') != '' \
                                                                 or registration.get('division') is not None else None
          saved_record.village =registration.get('village') if registration.get('village') != '' \
                                                               or registration.get('village') is not None else None
          saved_record.feature =registration.get('feature') if registration.get('feature') != '' \
                                                               or registration.get('feature') is not None else None
          saved_record.english =registration.get('english') if registration.get('english') != '' \
                                                               or registration.get('english') is not None else None
          saved_record.date_moved =registration.get('date_moved') if registration.get('date_moved') != '' \
                                                                     or registration.get('date_moved') is not None else None
          saved_record.languages =registration.get('languages') if registration.get('languages') != '' \
                                                                   or registration.get('languages') is not None else None
          saved_record.brac =registration.get('brac') if registration.get('brac') != '' \
                                                         or registration.get('brac') is not None else None
          saved_record.brac_chp =registration.get('brac_chp') if registration.get('brac_chp') != '' \
                                                                 or registration.get('brac_chp') is not None else None
          saved_record.education =registration.get('education') if registration.get('education') != '' \
                                                                   or registration.get('education') is not None else None
          saved_record.occupation =registration.get('occupation') if registration.get('occupation') != '' \
                                                                     or registration.get('occupation') is not None else None
          saved_record.community_membership =registration.get('community_membership') \
            if registration.get('community_membership') != '' or registration.get('community_membership') is not None else None
          saved_record.added_by =registration.get('added_by') if registration.get('added_by') != '' \
                                                                 or registration.get('added_by') is not None else None
          saved_record.comment =registration.get('comment') if registration.get('comment') != '' \
                                                               or registration.get('comment') is not None else None
          saved_record.proceed =registration.get('proceed') if registration.get('proceed') != '' \
                                                               or registration.get('proceed') is not None else None
          saved_record.client_time =registration.get('client_time') if registration.get('client_time') != '' \
                                                                       or registration.get('client_time') is not None else None
          saved_record.date_added =registration.get('date_added') if registration.get('date_added') != '' \
                                                                     or registration.get('date_added') is not None else None
          saved_record.synced =registration.get('synced') if registration.get('synced') != '' \
                                                             or registration.get('synced') is not None else None
          saved_record.archived = 0
          saved_record.chew_name =registration.get('chew_name') if registration.get('chew_name') != '' \
                                                                   or registration.get('chew_name') is not None else None
          saved_record.chew_number =registration.get('chew_number') if registration.get('chew_number') != '' \
                                                                       or registration.get('chew_number') is not None else None
          saved_record.ward =registration.get('ward') if registration.get('ward') != '' \
                                                         or registration.get('ward') is not None else None
          saved_record.cu_name =registration.get('cu_name') if registration.get('cu_name') != '' \
                                                               or registration.get('cu_name') is not None else None
          saved_record.link_facility =registration.get('link_facility') if registration.get('link_facility') != '' \
                                                                           or registration.get('link_facility') is not None else None
          saved_record.households =registration.get('households') if registration.get('households') != '' \
                                                                     or registration.get('households') is not None else None
          saved_record.trainings =registration.get('trainings') if registration.get('trainings') != '' \
                                                                   or registration.get('trainings') is not None else None
          saved_record.is_chv =registration.get('is_chv') if registration.get('is_chv') != '' \
                                                             or registration.get('is_chv') is not None else None
          saved_record.is_gok_trained =registration.get('is_gok_trained') \
            if registration.get('is_gok_trained') != '' or registration.get('is_gok_trained') is not None else None
          saved_record.referral =registration.get('referral') if registration.get('referral') != '' \
                                                                 or registration.get('referral') is not None else None
          saved_record.referral_number =registration.get('referral_number') \
            if registration.get('referral_number') != '' or registration.get('referral_number') is not None else None
          saved_record.referral_title =registration.get('referral_title') \
            if registration.get('referral_title') != '' or registration.get('referral_title') is not None else None
          saved_record.vht =registration.get('vht') if registration.get('vht') != '' \
                                                       or registration.get('vht') is not None else None
          saved_record.parish =registration.get('parish') if registration.get('parish') != '' \
                                                             or registration.get('parish') is not None else None
          saved_record.financial_accounts =registration.get('financial_accounts')\
            if registration.get('financial_accounts') != '' \
               or registration.get('financial_accounts') is not None else None
          saved_record.recruitment_transport =registration.get('recruitment_transport') \
            if registration.get('recruitment_transport') != '' or registration.get('recruitment_transport') \
               is not None else None
          saved_record.branch_transport =registration.get('branch_transport') if registration.get('branch_transport') != '' \
                                                                                 or registration.get('branch_transport') is not None else None
          saved_record.referral_id =registration.get('chew_id') if registration.get('chew_id') != '' \
                                                                   or registration.get('chew_id') is not None else None
          db.session.add(saved_record)
          db.session.commit()
          operation='updated'
        else:
          db.session.add(record)
          db.session.commit()
          operation='created'
        status.append({'id':record.id, 'status':'ok', 'operation':operation})
      return jsonify(status=status)
    else:
      return jsonify(error="No records posted")
    
@api.route('/synclink_facilities', methods=['GET', 'POST'])
@api.route('/sync/link_facilities', methods=['GET', 'POST'])
@api_login_required
def sync_link_facilities():
  if request.method == 'GET':
    records = LinkFacility.query.filter(LinkFacility.archived != 1)
    return jsonify({'link_facilities': [record.to_json() for record in records]})
  else:
    status = []
    link_facilities_list = request.json.get('link_facilities')
    if link_facilities_list is not None:
      for link_facility in link_facilities_list:
        saved_record = LinkFacility.query.filter(LinkFacility.id == link_facility.get('id')).first()
        lon = 0
        lat = 0
        if link_facility.get('lon') !='':
          lon = float(link_facility.get('lon'))
        if link_facility.get('lat') !='':
          lat = float(link_facility.get('lat'))
        if saved_record:
          saved_record.id = link_facility.get('id'),
          saved_record.facility_name = link_facility.get('facility_name'),
          saved_record.county = link_facility.get('county'),
          saved_record.lat = lat,
          saved_record.lon = lon,
          saved_record.subcounty = link_facility.get('subcounty'),
          saved_record.client_time = link_facility.get('date_added'),
          saved_record.addedby = link_facility.get('addedby'),
          saved_record.mrdt_levels = link_facility.get('mrdt_levels'),
          saved_record.act_levels = link_facility.get('act_levels'),
          saved_record.country = link_facility.get('country'),
          saved_record.facility_id = link_facility.get('facility_id'),
          saved_record.archived = 0
          operation = 'updated'
        else:
          saved_record = LinkFacility.from_json(link_facility)
          operation = 'created'
        db.session.add(saved_record)
        db.session.commit()
        status.append({'id': saved_record.id, 'status': 'ok', 'operation': operation})
      return jsonify(status=status)
    else:
      return jsonify(error="No records posted")

@api.route('/syncmapping', methods=['GET', 'POST'])
@api.route('/sync/mapping', methods=['GET', 'POST'])
@api_login_required
def sync_mapping():
  if request.method == 'GET':
    records = Mapping.query.filter(Mapping.archived != 1)
    return jsonify({'mappings': [record.to_json() for record in records]})
  else:
    status = []
    mapping_list = request.json.get('mappings')
    if mapping_list is not None:
      for mapping in mapping_list:
        record = Mapping.from_json(mapping)
        saved_record = Mapping.query.filter(Mapping.id == record.id).first()
        if saved_record:
          saved_record.name = mapping.get('name') if mapping.get('name') != '' else None
          saved_record.country = mapping.get('country') if mapping.get('country') != '' else None
          saved_record.county = mapping.get('county') if mapping.get('county') != '' else None
          saved_record.subcounty = mapping.get('subcounty') if mapping.get('subcounty') != '' else None
          saved_record.district = mapping.get('district') if mapping.get('district') != '' else None
          saved_record.added_by = mapping.get('added_by') if mapping.get('added_by') != '' else 1
          saved_record.contact_person = mapping.get('contact_person') if mapping.get('contact_person') != '' else None
          saved_record.phone = mapping.get('phone') if mapping.get('phone') != '' else None
          saved_record.synced = 1
          saved_record.comment = mapping.get('comment')
          operation = 'updated'
        else:
          operation = 'created'
          record.synced = 1
          db.session.add(record)
          db.session.commit()
          
        status.append({'id': record.id, 'status': 'ok', 'operation': operation})
      return jsonify(status=status)
    else:
      return jsonify(error=mapping_list)

@api.route('/syncparish', methods=['GET', 'POST'])
@api.route('/sync/parish', methods=['GET', 'POST'])
@api_login_required
def sync_parish():
  if request.method == 'GET':
    records = Parish.query.filter(Parish.archived != 1)
    return jsonify({'parish': [record.to_json() for record in records]})
  else:
    status = []
    parish_list = request.json.get('parishes')
    if parish_list is not None:
      for parish in parish_list:
        saved_record = Parish.query.filter(Parish.id == parish.get('id')).first()
        if saved_record:
          if parish.get('id') is not None or parish.get('id') != '':
            saved_record.id = parish.get('id')
          if parish.get('name') is not None or parish.get('name') != '':
            saved_record.name = parish.get('name')
          if parish.get('parent') is not None or parish.get('parent') != '':
            saved_record.parent = parish.get('parent')
          if parish.get('mapping') is not None or parish.get('mapping') != '':
            saved_record.mapping_id = parish.get('mapping')
          if parish.get('added_by') is not None or parish.get('added_by') != '':
            saved_record.added_by = parish.get('added_by')
          if parish.get('contact_person') is not None or parish.get('contact_person') != '':
            saved_record.contact_person = parish.get('contact_person')
          if parish.get('phone') is not None or parish.get('phone') != '':
            saved_record.phone = parish.get('phone')
          if parish.get('comment') is not None or parish.get('comment') != '':
            saved_record.comment = parish.get('comment')
          if parish.get('country') is not None or parish.get('country') != '':
            saved_record.country = parish.get('country')
          if parish.get('date_added') is not None or parish.get('date_added') != '':
            saved_record.client_time = parish.get('date_added')
          operation = 'updated'
        else:
          saved_record = Parish(
              id=parish.get('id'),
              name = parish.get('name'),
              parent = parish.get('parent') if parish.get('parent') != '' else None,
              mapping_id = parish.get('mapping') if parish.get('mapping') != '' else None,
              added_by = parish.get('added_by') if parish.get('added_by') != '' else None,
              contact_person = parish.get('contact_person'),
              phone = parish.get('phone'),
              comment = parish.get('comment'),
              country = parish.get('country') if parish.get('country') != '' else None,
              client_time = parish.get('date_added'),
          )
          operation = 'created'
        db.session.add(saved_record)
        db.session.commit()
        status.append({'id': saved_record.id, 'status': 'ok', 'operation': operation})
      return jsonify(status=status)
    else:
      return jsonify(error="No records posted")

@api.route('/syncvillages', methods=['GET', 'POST'])
@api.route('/sync/villages', methods=['GET', 'POST'])
@api_login_required
def sync_village():
  if request.method == 'GET':
    if request.args.get('parish'):
      return jsonify({'villages':[village.to_json() for village in Village.query.filter_by(archived=0, parish_id=request.args.get('parish'))]})
    else:
      return jsonify(villages=[record.to_json() for record in Village.query.filter_by(archived=0)])
  else:
    status = []
    village_list = request.json.get('villages')
    if village_list is not None:
      for village in village_list:
        saved_record = Village.query.filter(Village.id == village.get('id')).first()
        if saved_record:
          # update
          saved_record.id = village.get('id')
          saved_record.village_name = village.get('village_name')
          saved_record.mapping_id = village.get('mapping_id')
          saved_record.lat = village.get('lat')
          saved_record.lon = village.get('lon')
          saved_record.country = village.get('country')
          saved_record.district = village.get('district')
          saved_record.county = village.get('county')
          saved_record.sub_county_id = village.get('sub_county_id')
          saved_record.parish_id = village.get('parish')
          saved_record.community_unit_id = village.get('community_unit') if village.get('community_unit') !="" else None
          saved_record.ward = village.get('ward')
          saved_record.link_facility_id = village.get('link_facility_id') if village.get('link_facility_id') !="" else None
          saved_record.area_chief_name = village.get('area_chief_name')
          saved_record.area_chief_phone = village.get('area_chief_phone')
          saved_record.distancetobranch = village.get('distancetobranch')
          saved_record.transportcost = village.get('transportcost')
          saved_record.distancetomainroad = village.get('distancetomainroad')
          saved_record.noofhouseholds = village.get('noofhouseholds')
          saved_record.mohpoplationdensity = village.get('mohpoplationdensity')
          saved_record.estimatedpopulationdensity = village.get('estimatedpopulationdensity')
          saved_record.economic_status = village.get('economic_status')
          saved_record.distancetonearesthealthfacility = village.get('distancetonearesthealthfacility')
          saved_record.actlevels = village.get('actlevels')
          saved_record.actprice = village.get('actprice')
          saved_record.mrdtlevels = village.get('mrdtlevels')
          saved_record.mrdtprice = village.get('mrdtprice')
          saved_record.presenceofhostels = village.get('presenceofhostels')
          saved_record.presenceofestates = village.get('presenceofestates')
          saved_record.number_of_factories = village.get('number_of_factories')
          saved_record.presenceofdistibutors = village.get('presenceofdistibutors')
          saved_record.name_of_distibutors = village.get('name_of_distibutors')
          saved_record.tradermarket = village.get('tradermarket')
          saved_record.largesupermarket = village.get('largesupermarket')
          saved_record.ngosgivingfreedrugs = village.get('ngosgivingfreedrugs')
          saved_record.ngodoingiccm = village.get('ngodoingiccm')
          saved_record.ngodoingmhealth = village.get('ngodoingmhealth')
          saved_record.nameofngodoingiccm = village.get('nameofngodoingiccm')
          saved_record.nameofngodoingmhealth = village.get('nameofngodoingmhealth')
          saved_record.privatefacilityforact = village.get('privatefacilityforact')
          saved_record.privatefacilityformrdt = village.get('privatefacilityformrdt')
          saved_record.synced = village.get('synced')
          saved_record.chvs_trained = village.get('chvs_trained')
          saved_record.client_time = village.get('dateadded')
          saved_record.addedby = village.get('addedby')
          saved_record.comment = village.get('comment')
          saved_record.brac_operating = village.get('brac_operating')
          saved_record.mtn_signal = village.get('mtn_signal')
          saved_record.safaricom_signal = village.get('safaricom_signal')
          saved_record.airtel_signal = village.get('airtel_signal')
          saved_record.orange_signal = village.get('orange_signal')
          saved_record.act_stock = village.get('act_stock')
          operation = 'updated'
        else:
          saved_record = Village(
              id = village.get('id'),
              village_name = village.get('village_name'),
              mapping_id = village.get('mapping_id'),
              lat = village.get('lat'),
              lon = village.get('lon'),
              country = village.get('country'),
              district = village.get('district'),
              county = village.get('county'),
              sub_county_id = village.get('sub_county_id'),
              parish_id = village.get('parish'),
              community_unit_id = village.get('community_unit') if village.get(
                'community_unit') != "" else None,
              ward = village.get('ward'),
              link_facility_id = village.get('link_facility_id') if village.get(
                'link_facility_id') != "" else None,
              area_chief_name = village.get('area_chief_name'),
              area_chief_phone = village.get('area_chief_phone'),
              distancetobranch = village.get('distancetobranch'),
              transportcost = village.get('transportcost'),
              distancetomainroad = village.get('distancetomainroad'),
              noofhouseholds = village.get('noofhouseholds'),
              mohpoplationdensity = village.get('mohpoplationdensity'),
              estimatedpopulationdensity = village.get('estimatedpopulationdensity'),
              economic_status = village.get('economic_status'),
              distancetonearesthealthfacility = village.get('distancetonearesthealthfacility'),
              actlevels = village.get('actlevels'),
              actprice = village.get('actprice'),
              mrdtlevels = village.get('mrdtlevels'),
              mrdtprice = village.get('mrdtprice'),
              presenceofhostels = village.get('presenceofhostels'),
              presenceofestates = village.get('presenceofestates'),
              number_of_factories = village.get('number_of_factories'),
              presenceofdistibutors = village.get('presenceofdistibutors'),
              name_of_distibutors = village.get('name_of_distibutors'),
              tradermarket = village.get('tradermarket'),
              largesupermarket = village.get('largesupermarket'),
              ngosgivingfreedrugs = village.get('ngosgivingfreedrugs'),
              ngodoingiccm = village.get('ngodoingiccm'),
              ngodoingmhealth = village.get('ngodoingmhealth'),
              nameofngodoingiccm = village.get('nameofngodoingiccm'),
              nameofngodoingmhealth = village.get('nameofngodoingmhealth'),
              privatefacilityforact = village.get('privatefacilityforact'),
              privatefacilityformrdt = village.get('privatefacilityformrdt'),
              synced = village.get('synced'),
              chvs_trained = village.get('chvs_trained'),
              client_time = village.get('dateadded'),
              addedby = village.get('addedby'),
              comment = village.get('comment'),
              brac_operating = village.get('brac_operating'),
              mtn_signal = village.get('mtn_signal'),
              safaricom_signal = village.get('safaricom_signal'),
              airtel_signal = village.get('airtel_signal'),
              orange_signal = village.get('orange_signal'),
              act_stock = village.get('act_stock'),
          )
          operation = 'created'
        db.session.add(saved_record)
        db.session.commit()
        status.append({'id': saved_record.id, 'status': 'ok', 'operation': operation})
      return jsonify(status=status)
    else:
      return jsonify(error="No records posted")

@api.route('/syncpartners', methods=['GET', 'POST'])
@api.route('/sync/partners', methods=['GET', 'POST'])
@api_login_required
def sync_partner():
  if request.method == 'GET':
    records = Partner.query.filter(Partner.archived != 1)
    return jsonify({'partners': [record.to_json() for record in records]})
  else:
    status = []
    partner_list = request.json.get('partners')
    if partner_list is not None:
      for partner in partner_list:
        saved_record = Partner.query.filter(Partner.id == partner.get('id')).first()
        if saved_record:
          saved_record.client_time = partner.get('date_added')
          operation = 'updated'
        else:
          operation = 'created'
        db.session.add(saved_record)
        db.session.commit()
        status.append({'id': saved_record.id, 'status': 'ok', 'operation': operation})
      return jsonify(status=status)
    else:
      return jsonify(error="No records posted")


@api.route('/synccommunity_unit', methods=['GET', 'POST'])
@api.route('/sync/community_unit', methods=['GET', 'POST'])
@api_login_required
def sync_cu():
  if request.method == 'GET':
    records = CommunityUnit.query.filter_by(archived = 0)
    return jsonify({'community_units': [record.to_json() for record in records]})
  else:
    status = []
    community_unit_list = request.json.get('community_unit')
    if community_unit_list is not None:
      for cu in community_unit_list:
        saved_record = CommunityUnit.query.filter(CommunityUnit.id == cu.get('id')).first()
        if saved_record:
          saved_record.client_time = cu.get('date_added')
          saved_record.id = cu.get('id')
          saved_record.name = cu.get('name')
          saved_record.mappingid = cu.get('mappingid') if cu.get('mappingid') !='' else None,
          saved_record.lat = cu.get('lat')
          saved_record.lon = cu.get('lon')
          saved_record.country = cu.get('country')
          saved_record.subcountyid = cu.get('subcountyid') if cu.get('subcountyid') !='' else None,
          saved_record.linkfacilityid = cu.get('linkfacilityid') if cu.get('linkfacilityid') !='' else None,
          saved_record.areachiefname = cu.get('areachiefname')
          saved_record.ward = cu.get('ward')
          saved_record.economicstatus = cu.get('economicstatus')
          saved_record.privatefacilityforact = cu.get('privatefacilityforact')
          saved_record.privatefacilityformrdt = cu.get('privatefacilityformrdt')
          saved_record.nameofngodoingiccm = cu.get('nameofngodoingiccm')
          saved_record.nameofngodoingmhealth = cu.get('nameofngodoingmhealth')
          saved_record.client_time = cu.get('client_time')
          saved_record.date_added = cu.get('date_added')
          saved_record.addedby = cu.get('addedby')
          saved_record.numberofchvs = cu.get('numberofchvs')
          saved_record.householdperchv = cu.get('householdperchv')
          saved_record.numberofvillages = cu.get('numberofvillages')
          saved_record.distancetobranch = cu.get('distancetobranch')
          saved_record.transportcost = cu.get('transportcost')
          saved_record.distancetomainroad = cu.get('distancetomainroad')
          saved_record.noofhouseholds = cu.get('noofhouseholds')
          saved_record.mohpoplationdensity = cu.get('mohpoplationdensity')
          saved_record.estimatedpopulationdensity = cu.get('estimatedpopulationdensity')
          saved_record.distancetonearesthealthfacility = cu.get('distancetonearesthealthfacility')
          saved_record.actlevels = cu.get('actlevels')
          saved_record.actprice = cu.get('actprice')
          saved_record.mrdtlevels = cu.get('mrdtlevels')
          saved_record.mrdtprice = cu.get('mrdtprice')
          saved_record.noofdistibutors = cu.get('noofdistibutors')
          saved_record.chvstrained = cu.get('chvstrained')
          saved_record.presenceofestates = cu.get('presenceofestates')
          saved_record.presenceoffactories = cu.get('presenceoffactories')
          saved_record.presenceofhostels = cu.get('presenceofhostels')
          saved_record.tradermarket = cu.get('tradermarket')
          saved_record.largesupermarket = cu.get('largesupermarket')
          saved_record.ngosgivingfreedrugs = cu.get('ngosgivingfreedrugs')
          saved_record.ngodoingiccm = cu.get('ngodoingiccm')
          saved_record.ngodoingmhealth = cu.get('ngodoingmhealth')
          saved_record.comment = cu.get('comment')
          saved_record.archived = cu.get('archived')
          operation = 'updated'
        else:
          saved_record = CommunityUnit.from_json(cu)
          operation = 'created'
        db.session.add(saved_record)
        db.session.commit()
        status.append({'id': saved_record.id, 'status': 'ok', 'operation': operation})
      return jsonify(status=status)
    else:
      return jsonify(error="No records posted")


@api.route('/syncpartners/activity', methods=['GET', 'POST'])
@api.route('/sync/partners/activity', methods=['GET', 'POST'])
@api_login_required
def sync_partner_cu():
  if request.method == 'GET':
    records = PartnerActivity.query.filter(PartnerActivity.archived != 1)
    return jsonify({'partner_cu': [record.to_json() for record in records]})
  else:
    status = []
    partner_cu_list = request.json.get('partners_cu')
    if partner_cu_list is not None:
      for partner_cu in partner_cu_list:
        saved_record = PartnerActivity.query.filter(PartnerActivity.id == partner_cu.get('id')).first()
        if saved_record:
          saved_record.client_time = partner_cu.get('date_added')
          operation = 'updated'
        else:
          operation = 'created'
        db.session.add(saved_record)
        db.session.commit()
        status.append({'id': saved_record.id, 'status': 'ok', 'operation': operation})
      return jsonify(status=status)
    else:
      return jsonify(error="No records posted")


@api.route('/syncinterviews', methods=['GET', 'POST'])
@api.route('/sync/interviews', methods=['GET', 'POST'])
@api_login_required
def sync_interviews():
  if request.method == 'GET':
    records  = Interview.query.filter(Interview.archived != 1)
    return jsonify({'interviews':[record.to_json() for record in records]})
  else:
    status = []
    interview_list = request.json.get('interviews')
    if interview_list is not None:
      for interview in interview_list:
        record = Interview.from_json(interview)
        saved_record  = Interview.query.filter(Interview.id == record.id).first()
        if saved_record:
          saved_record.id = interview.get('id')
          saved_record.applicant = interview.get('applicant')
          saved_record.recruitment = interview.get('recruitment')
          saved_record.motivation = interview.get('motivation')
          saved_record.community = interview.get('community')
          saved_record.mentality = interview.get('mentality')
          saved_record.country = interview.get('country')
          saved_record.selling = interview.get('selling')
          saved_record.health = interview.get('health')
          saved_record.investment = interview.get('investment')
          saved_record.interpersonal = interview.get('interpersonal')
          saved_record.canjoin = interview.get('canjoin')
          saved_record.commitment = interview.get('commitment')
          saved_record.total = interview.get('total')
          saved_record.selected = interview.get('selected')
          saved_record.synced = interview.get('synced')
          saved_record.added_by = interview.get('added_by')
          saved_record.comment = interview.get('comment')
          saved_record.client_time = interview.get('client_time')
          saved_record.date_added = interview.get('date_added')
          saved_record.archived = interview.get('archived')
          operation = 'updated'
          db.session.add(saved_record)
        else:
          operation = 'created'
          db.session.add(record)
        db.session.commit()
          
        status.append({'id':record.id, 'status':'ok', 'operation':operation})
      return jsonify(status=status)
    else:
      return jsonify(error="No records posted")


@api.route('/syncexams', methods=['GET', 'POST'])
@api.route('/sync/exams', methods=['GET', 'POST'])
@api_login_required
def sync_exams():
  if request.method == 'GET':
    records  = Exam.query.filter(Exam.archived != 1)
    return jsonify({'exams':[record.to_json() for record in records]})
  else:
    status = []
    exam_list = request.json.get('exams')
    if exam_list is not None:
      for exam in exam_list:
        record = Exam.from_json(exam)
        saved_record  = Exam.query.filter(Exam.id == record.id).first()
        if saved_record:
          saved_record.id =exam.get('id')
          saved_record.applicant = exam.get('applicant')
          saved_record.recruitment = exam.get('recruitment')
          saved_record.country = exam.get('country')
          saved_record.math = exam.get('math')
          saved_record.personality = exam.get('personality')
          saved_record.english = exam.get('english')
          saved_record.added_by = exam.get('added_by')
          saved_record.comment = exam.get('comment')
          saved_record.client_time = exam.get('client_time')
          saved_record.archived = 0
          db.session.add(saved_record)
          db.session.commit()
          operation='updated'
        else:
          print 'Creating exam'
          db.session.add(record)
          db.session.commit()
          operation='created'
        status.append({'id':record.id, 'status':'ok', 'operation':operation})
      return jsonify(status=status)
    else:
      return jsonify(error="No records posted")


@api.route('/synclocations', methods=['GET', 'POST'])
@api.route('/sync/locations', methods=['GET', 'POST'])
@api_login_required
def sync_locations():
  if request.method == 'GET':
    locations = Location.query.filter(Location.archived == 0)
    return jsonify({'locations': [location.to_json() for location in locations]})
  
  
@api.route('/get/locations', methods=['GET', 'POST'])
@api_login_required
def get_locations():
  if request.method == 'GET':
    locations = Location.query.filter(Location.archived == 0)
    return Response(json.dumps([location.to_json() for location in locations]), mimetype='application/json')


@api.route('/create/ke/counties')
@api_login_required
def create_ke_counties():
  with open(os.path.dirname(os.path.abspath(data.__file__))+'/kenya_county.csv', 'r') as f:
    for row in csv.reader(f.read().splitlines()):
      county = County(id=row[0], name=row[1], archived=0)
      db.session.add(county)
      db.session.commit()
  return jsonify(status='ok')


@api.route('/synccounties', methods=['GET', 'POST'])
@api.route('/sync/counties', methods=['GET', 'POST'])
@api_login_required
def sync_counties():
  if request.method == 'GET':
    locations = Location.query.filter(Location.archived == 0)
    if request.args.get('country'):
      country = request.args.get('country')
      locations = Location.query.filter_by(archived=0, admin_name='County', country=country.upper())
      return jsonify({'locations': [location.to_json() for location in locations]})
    # country = request.args.get('country')
    locations = Location.query.filter_by(archived=0, admin_name='County')
    return jsonify({'locations': [location.to_json() for location in locations]})

@api.route('/sync/gpsdata', methods=['GET', 'POST'])
@api_login_required
def sync_gps_data():
  if request.method == 'GET':
    records  = GpsData.query.all()
    return jsonify({'gps':[record.to_json() for record in records]})
  else:
    status = []
    gps_list = request.json.get('gps')
    if gps_list is not None:
      for gps in gps_list:
        record = GpsData.from_json(gps)
        saved_record  = GpsData.query.filter(GpsData.id == record.id).first()
        if saved_record:
          pass
        else:
          db.session.add(record)
          db.session.commit()
        status.append({'id':record.id, 'status':'ok', 'operation':'saved'})
      return jsonify(status=status)
    else:
      return jsonify(error="No records posted")

@api.route('/sync/chew_referral', methods=['GET', 'POST'])
@api_login_required
def sync_chew_referral():
  if request.method == 'GET':
    records  = Referral.query.all()
    return jsonify({'referrals':[record.to_json() for record in records]})
  else:
    status = []
    referral_list = request.json.get('chew_referrals')
    if referral_list is not None:
      for referral in referral_list:
        record = Referral.from_json(referral)
        saved_record  = Referral.query.filter(Referral.id == record.id).first()
        if saved_record:
          # update the referral
          pass
        else:
          db.session.add(record)
          db.session.commit()
        status.append({'id':record.id, 'status':'ok', 'operation':'saved'})
      return jsonify(status=status)
    else:
      return jsonify(error="No records posted")

@api.route('/sync/iccm-components', methods=['GET', 'POST'])
@api_login_required
def sync_iccm_components():
  if request.method == 'GET':
    iccms = IccmComponents.query.filter_by(archived=0)
    return jsonify({'components': [r.to_json() for r in iccms]})
  else:
    return jsonify(error="No records posted")


@api.route('/sync/ke-subcounties', methods=['GET', 'POST'])
@api_login_required
def sync_ke_subcounties():
  ke_subcounties = data.get_ke_subcounties()
  return jsonify(subcounties=ke_subcounties)


@api.route('/sync/ke/wards', methods=['GET', 'POST'])
@api_login_required
def sync_ke_wards():
  wards = Ward.query.filter_by(archived=0)
  return jsonify(wards=[ward.to_json() for ward in wards])


@api.route('/get/training-data', methods=['GET', 'POST'])
@api_login_required
def get_training_data():
  """
    Returns Json Payload for the recruitments, and only the selected Applicants
  """
  if request.method == 'GET':
    interviews = Interview.query.filter_by(selected=1)
    trainings=[]
    recruitments={}
    for interview in interviews:
      if interview.recruitment not in recruitments:
        data_count = Registration.query.filter_by(id=interview.recruitment)
        recruitments[interview.recruitment] = interview.base_recruitment.to_json()
        recruitments[interview.recruitment]['data']['count'] = data_count.count()
        recruitments[interview.recruitment]['data']['registrations'] = []
      recruitments[interview.recruitment]['data']['registrations'].append(interview.registration.to_json())
    return jsonify(draft_trainings=recruitments)
  else:
    return jsonify(message='not allowed'), 403

@api.route('/recruitment-data/<string:id>', methods=['GET', 'POST'])
@api_login_required
def get_recruitmet_data(id):
  if request.method == 'GET':
    registrations = Registration.query.filter_by(recruitment=id).all()
    return jsonify({'qualified_chps': [r.to_json() for r in registrations]})
  else:
    return jsonify(error="No records posted")

@api.route('/sync/trainings', methods=['GET', 'POST'])
@api_login_required
def get_trainings():
  """
    Returns Json Payload for the training data
  """
  if request.method == 'GET':
    trainings = Training.query.filter_by(archived=0)
    return jsonify(trainings=[r.to_json() for r in trainings])
  else:
    return jsonify(message='not allowed'), 403
  
@api.route('/get/trainers', methods=['GET'])
@api_login_required
def get_trainers():
  """
  Get all trainers
  """
  if request.args.get('term'):
    return jsonify(trainers=[trainer.to_json() for trainer in User.query.filter_by(confirmed=True, archived=0)
                   .filter(User.name.ilike('%{}%'.format(request.args.get('term'))))])
  else:
    return jsonify(trainers=[trainer.to_json() for trainer in User.query.filter_by(confirmed=True, archived=0)])

@api.route('/sync/training-classes', methods=['GET', 'POST'])
@api_login_required
def sync_training_classes():
  """
  Syncs training classes at the cloud and in the mobile app
  """
  if request.method == 'GET':
    records = TrainingClasses.query.all()
    return jsonify({'training-classes': [record.to_json for record in records]})
  else:
    status = []
    training_classes = request.json.get('training_classes')
    if training_classes is not None:
      for training_class in training_classes:
        record = TrainingClasses.from_json(training_class)
        saved_record = TrainingClasses.query.filter(TrainingClasses.id == record.id).first()
        if saved_record:
          saved_record.id = training_class.get('id')
          saved_record.class_name = training_class.get('class_name')
          saved_record.created_by = training_class.get('created_by')
          saved_record.client_time = training_class.get('client_time')
          saved_record.date_created = training_class.get('date_created')
          db.session.add(record)
          db.session.commit()
          operation = 'updated'
        else:
          db.session.add(record)
          db.session.commit()
          operation = 'added'
        status.append({'id': record.id, 'status': 'ok', 'operation': operation})
      return jsonify(status=status)
    else:
      return jsonify(message='No records posted')


@api.route('/sync/<string:training_id>/trainees', methods=['GET', 'POST'])
@api.route('/sync/trainees', methods=['GET', 'POST'])
@api_login_required
def sync_trainees(training_id=None):
  """
  Syncs trainees to and from the cloud
  """
  if request.method == 'GET':
    if training_id:
      records = Trainees.query.filter_by(training_id=training_id).all()
    else:
      records = Trainees.query.all()
    return jsonify({'trainees': [record.to_json() for record in records]})
  else:
    status = []
    trainees = request.json.get('trainees')
    if trainees is not None:
      for trainee in trainees:
        record = Trainees.from_json(trainee)
        saved_record = Trainees.query.filter(Trainees.id == record.id).first()
        if saved_record:
          saved_record.id = trainee.get('id')
          saved_record.registration_id = trainee.get('registration_id')
          saved_record.class_id = trainee.get('class_id')
          saved_record.training_id = trainee.get('training_id')
          db.session.add(record)
          db.session.commit()
          operation = 'updated'
        else:
          db.session.add(record)
          db.session.commit()
          operation = 'added'
        status.append({'id': record.id, 'status': 'ok', 'operation': operation})
        return jsonify(status=status)
      else:
        return jsonify(message='No records posted')


@api.route('/get/mapping-details/<string:id>', methods=['GET', 'POST'])
@api_login_required
def get_mapping_details_summary(id):
  """
  Get a summary of the mapping details
  """
  if request.method == 'GET':
    mapping = Mapping.query.filter_by(id=id).first().to_json()
    mapping['parishes']=[]
    parishes = Parish.query.filter_by(mapping_id=id)
    for parish in parishes:
      parish_data = parish.to_json()
      villages = Village.query.filter_by(parish_id=parish.id)
      if not parish_data.has_key('village_data'):
        parish_data['village_data'] = {}
      parish_data['village_data']['count'] = villages.count()
      parish_data['village_data']['villages'] = [village.to_json() for village in villages]
      mapping['parishes'].append(parish_data)
    return jsonify(mappings=mapping)

@api.route('/sync/education', methods=['GET','POST'])
@api_login_required
def get_education():
  return jsonify(education=[e.to_json() for e in Education.query.filter_by(archived=0)])

# @api.route('/sync/trainee-status', methods=['GET','POST'])
@api.route('/exams', methods=['GET', 'POST'])
@api_login_required
def get_exams():
  if request.method == 'GET':
    exams = []
    exams_data = ExamTraining.query.filter_by(archived=False)
    for exam in exams_data:
      exams.append(exam_with_questions_to_dict(exam))
    return jsonify(exams=exams)
  else:
    json_data = request.json
    new_exam = ExamTraining(**json_data) if json_data.get('id') is not None else None
    exam = ExamTraining.query.filter_by(id=json_data.get('id')).first() if json_data.get('id') is not None else None
    if exam is not None:
      db.session.merge(new_exam)
    elif new_exam is not None:
      db.session.add(new_exam)
    db.session.commit()
    return jsonify(status='ok')


@api.route('/questions', methods=['GET', 'POST'])
@api.route('/questions/<int:question_id>', methods=['GET', 'POST'])
@api_login_required
def get_questions(question_id = None):
  if request.method == 'GET':
    
    term = request.args.get('term', None)
    
    if question_id:
      records = Question.query.filter_by(id=question_id, archived=False)
    else:
      if term:
        records = Question.query.filter(Question.archived == False, Question.question.ilike('%{}%'.format(term)))
      else:
        records = Question.query.filter_by(archived=False)
    return jsonify({'questions': [{'question': record.question, 'id': record.id,
                                   'allocated_marks': record.allocated_marks,
                                   'question_type_id': record.question_type_id,
                                   'choices': [choice.to_json() for choice in record.choices]}
                                  for record in records]})
  else:
    """
    Question Object will come in the form of json object, with choices as a list
    """
    json_data = request.json
    question_list = request.json.get('questions')
    if question_list is not None:
      status = save_questions(question_list)
      return jsonify(status=status)
    return jsonify(message='no question posted')


@api.route('/exam/<string:exam_id>', methods=['GET', 'POST'])
@api_login_required
def get_exam_details(exam_id):
  if request.method == 'GET':
    # get the exam
    exam = ExamTraining.query.filter_by(id=exam_id, archived=False).first_or_404()
    exam = exam._asdict()
    exam_questions = ExamQuestion.query.filter_by(exam_id=exam_id, archived=False)
    exam['questions'] = [{'question': record.question.question, 'id': record.question.id, 'allocated_marks':
      record.question.allocated_marks,
                          'question_type_id': record.question.question_type_id,
                          'choices': [choice.to_json() for choice in record.question.choices]}
                         for record in exam_questions]
    return jsonify(examination=exam)


@api.route('/exam/status', methods=['GET', 'POST'])
@api_login_required
def get_exam_status():
  if request.method == 'GET':
    # get the exam status
    return jsonify(exam_statuses=[{'id': status.id, 'title': status.title}
                                  for status in ExamStatus.query.filter_by(archived=False)])
  else:
    data = request.json
    new_status = ExamStatus(**data)
    existing_status = ExamStatus.query.filter_by(id=data.get('id')).first() if data.get('id') is not None else None
    db.session.merge(new_status) if existing_status is not None else db.session.add(new_status)
    db.session.commit()
    return jsonify(status='ok')


@api.route('/question/topics', methods=['GET', 'POST'])
@api.route('/question/<string:question_id>/topics', methods=['GET', 'POST'])
@api_login_required
def question_topics(question_id = None):
  if request.method == 'GET':
    if question_id is None:
      question_topics = QuestionTopic.query.filter_by(archived=False)
    else:
      question_topics = QuestionTopic.query.filter_by(archived=False, question_id=question_id)
    return jsonify(question_topics=[{'id': topic.session_topic.id, 'topic': topic.session_topic.name}
                                    for topic in question_topics])
  else:
    data = request.json
    new_topic = QuestionTopic(**data)
    existing_topic = QuestionTopic.query.filter_by(id=data.get('id')).first() if data.get('id') is not None else None
    db.session.merge(new_topic) if existing_topic is not None else db.session.add(new_topic)
    db.session.commit()
    return jsonify(status='ok')

@api.route('/question_type', methods=['GET', 'POST'])
@api_login_required
def question_types():
  if request.method == 'GET':
    return jsonify(question_types=[q_type._asdict() for q_type in QuestionType.query.filter_by(archived=False)])
  else:
    data = request.json
    new_type = QuestionType(**data)
    existing_type = QuestionType.query.filter_by(id=data.get('id')).first() if data.get('id') is not None else None
    db.session.merge(new_type) if existing_type is not None else db.session.add(new_type)
    db.session.commit()
    return jsonify(status='ok')


@api.route('/training/<string:training_id>/exams', methods=['GET', 'POST'])
@api_login_required
def training_exams(training_id = None):
  if request.method == 'GET':
    if training_id is None:
      return jsonify(error="training id is required"), 400
    exams = []
    training_exams = TrainingExam.query.filter_by(training_id=training_id)
    for training_exam in training_exams:
      exam = exam_with_questions_to_dict(training_exam.exam)
      exam.update(training_exam._asdict())
      exams.append(exam)
    return jsonify(exams=exams)
  else:
    abort(405)
    
    
@api.route('/training_roles', methods=['GET', 'POST'])
@api_login_required
def training_roles():
  if request.method == 'GET':
    return jsonify(roles=[role._asdict() for role in TrainingRoles.query.filter_by(archived=0)])
  else:
    abort(405)
  
  
@api.route("/training/exam/result/save", methods=['POST'])
@api_login_required
def exam_result_save():
  try:
    data = request.json
    
    if not data:
      return jsonify(status=False, message="Invalid request"), 400
    
    for datum in data:
      exam_result = ExamResult.from_json(datum)
      db.session.add(exam_result) if exam_result.id is not None else db.session.merge(exam_result)
      
    db.session.commit()
    return jsonify(status=True, message="Saved Successfully"), 200
    
  except Exception as e:
    db.session.rollback()
    return jsonify(status=False, message="Unexpected error occured. Please try again"), 500
  finally:
    db.session.close()


@api.route('/training/<string:training_id>/trainers', methods=['GET', 'POST'])
@api_login_required
def training_trainers(training_id = None):
  if request.method == 'GET':
    if training_id is None:
      return jsonify(error="training id is required"), 400
    return jsonify(trainers=[trainer._asdict() for trainer in TrainingTrainers.query.filter_by(training_id=training_id)])
  else:
    trainers = request.json
    status = []
    for trainer in trainers:
      #check if the trainer exits
      existing_trainer = TrainingTrainers.query.filter_by(training_id=trainer.get('training_id'), trainer_id=trainer.get('trainer_id')).first()
      if existing_trainer:
        existing_trainer.archived=0
        existing_trainer.training_role_id=trainer.get('training_role_id')
        existing_trainer.country = Training.query.filter_by(id=training_id).first().country
        db.session.add(existing_trainer)
        db.session.commit()
        status.append({'record':trainer, 'operation':"updated"})
      else:
        trainer = TrainingTrainers(**trainer)
        trainer.country = Training.query.filter_by(id=training_id).first().country
        
        db.session.add(trainer)
        db.session.commit()
        status.append({'record': trainer, 'operation': "created"})
    return jsonify(status='ok', eperation=status)
      
    
def process_exam_csv(path):
  questions = process_csv(path, False)
  csv_questions = []
  meta_data = Question.__table__.columns.keys()
  for question in questions:
    answer = question.get('answer')
    # also append default meta for the question
    for meta in meta_data:
      question[meta] = question.get(meta)
    choices = []
    for key in question.keys():
      if key not in meta_data and key.startswith('choice') and question.get(key).strip() != "":
        choices.append({'choice': question.get(key), 'is_answer': True if key == answer else False})
        question.pop(key)
      question['choices'] = choices
    csv_questions.append(question)
  return csv_questions


def create_question_list(path):
  # validate the file
  
  if not os.path.isfile(path):
    return {'errors': ['File not valid'], 'status': 'failed', 'batch_id': None}
  question_list = process_exam_csv(path)
  return save_questions(question_list)


def save_questions(question_list):
  errors = []
  if question_list is not None:
    batch_id = str(uuid.uuid4()),
    for question_data in question_list:
      choices = question_data.get('choices')
      question = Question.query.filter_by(id=question_data.get('id')).first() if question_data.get(
          'id') is not None else None
      if question:
        question.question = question_data.get('question')
        question.allocated_marks = question_data.get('allocated_marks')
        question.question_type_id = question_data.get('question_type_id')
        question.created_by = question_data.get('created_by')
        question.date_created = question_data.get('date_created')
        question.archived = question_data.get('archived')
        question_id = question.id
        question.batch_id = batch_id
        db.session.commit()
      else:
        new_question = Question(
            question=question_data.get('question'),
            allocated_marks=question_data.get('allocated_marks'),
            question_type_id=question_data.get('question_type_id'),
            created_by=question_data.get('created_by'),
            date_created=question_data.get('date_created'),
            archived=question_data.get('archived'),
            batch_id=batch_id
        )
        db.session.add(new_question)
        db.session.commit()
        question_id = new_question.id
      # Create choices
      for choice in choices:
        # check if the choice exists
        q_choice = QuestionChoice.query.filter_by(question_id=question_id,
                                                  question_choice=choice.get('choice'))
        if q_choice is not None:
          new_question_choice = QuestionChoice(
              id=choice.get('id') if choice.get('id') is not None else None,
              question_id=question_id,
              question_choice=choice.get('choice'),
              is_answer=choice.get('is_answer'),
              allocated_marks=choice.get('allocated_marks'),
              created_by=choice.get('created_by'),
              date_created=choice.get('date_created'),
              archived=choice.get('archived'))
          db.session.add(new_question_choice)
        else:
          q_choice.question_id = question_id,
          q_choice.question_choice = choice.get('choice'),
          q_choice.is_answer = choice.get('is_answer'),
          q_choice.allocated_marks = choice.get('allocated_marks'),
          q_choice.created_by = choice.get('created_by'),
          q_choice.date_created = choice.get('date_created'),
          q_choice.archived = choice.get('archived')
          db.session.add(q_choice)
        db.session.commit()
    return {'errors': None, 'status': 'ok', 'batch_id': batch_id, 'data': data}
  else:
    errors.append('The question list is empty')
    return {'errors': errors, 'status': 'failed', 'csv_id': None}
  
  
def get_training_status():
  return jsonify(training_status=[st.to_json() for st in TraineeStatus.query.filter_by(archived=0)])

def generate_training_classes(recruitment):
  # determine the number of classes
  # count the number of items in the __dict__
  # Based on the country, generate the number of classes
  # The classes in each country have a set numnber of trainees.
  count = recruitment.get('data').get('count')
  number_of_classes = 1
  class_details={}
  trainees = recruitment.get('data').get('registrations')
  if recruitment.get('country') == "KE" or recruitment.get('country') == 'UG':
    if count <= 35:
      if len(trainees) > 0:
        class_details[1]= {[trainee.get('id') for trainee in trainees]}
    elif count > 35 and count <= 70:
      number_of_classes = 2
      class_1 = []
      class_2 = []
      x = 1
      for trainee in trainees:
        if x==1:
          class_1.append(trainee.get('id'))
          x += 1
        elif x==2:
          class_2.append(trainee.get('id'))
          x = 1
      class_details[1] = class_1
      class_details[2] = class_2
    elif count > 70 and count <= 105:
      number_of_classes = 3
      class_1= []
      class_2= []
      class_3 = []
      x=1
      for trainee in trainees:
        if x == 1:
          class_1.append(trainee.get('id'))
          x += 1
        elif x == 2:
          class_2.append(trainee.get('id'))
          x+=1
        else:
          class_3.append(trainee.get('id'))
          x=1
      class_details[1] = class_1
      class_details[2] = class_2
      class_details[3] = class_3
    return {"classes": number_of_classes, 'details':class_details}
  else:
    return {'count': recruitment.get('data').get('count'), 'len': len(recruitment.get('data').get('registrations'))}

def create_training(recruitment_id):
  recruitment = Recruitments.query.filter_by(id=recruitment_id).first()
  training = Training.query.filter_by(recruitment_id=recruitment.id).first()
  if not training:
    training = Training(
        id=str(uuid.uuid4()),
        training_name=recruitment.name,
        country=recruitment.country,
        district=recruitment.district,
        recruitment_id=recruitment.id,
        training_status_id=1,
        client_time=time.time(),
    )
    if recruitment.country == 'KE':
      if recruitment.subcounty_id is not None:
        training.subcounty_id = recruitment.subcounty_id
      if recruitment.county_id is not None:
        training.county_id = recruitment.county_id
    else:
      if recruitment.location_id is not None:
        training.location_id = recruitment.location_id
  db.session.add(training)
  db.session.commit()
  return training

def create_training_topics(training):
  session_topics = SessionTopic.query.filter_by(country=training.country, archived=0)
  for topic in session_topics:
    training_session = TrainingSession.query.filter_by(country=training.country, training_id=training.id,
                                                       session_topic_id=topic.id, archived=0).first()
    if not training_session:
      training_session = TrainingSession(
          id=str(uuid.uuid4()),
          training_id=training.id,
          session_topic_id=topic.id,
          country=training.country,
          created_by=1
      )
    db.session.add(training_session)
    db.session.commit()



