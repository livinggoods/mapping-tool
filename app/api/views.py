from . import api
from flask_login import login_required, current_user
from flask import Response, request, jsonify
import json
from sqlalchemy import func, distinct, select, exists, and_
from .. import db
from ..models import (Permission, Role, User, Geo, UserType, Village, LocationTargets,
    Location, Education, EducationLevel, Referral, Chp, Recruitments, Interview, Exam,
    SelectedApplication, Application, ApplicationPhone, Branch, Cohort, Registration)


@api.route('/firm_summary')
@login_required
def firm_summary():
    summary = current_user.firm_summary()
    return Response(json.dumps(summary, indent=4), mimetype='application/json')

@api.route('/recruitments.json')
def recruitments_json():
  if request.method == 'GET':
    page={'title':'Recruitments', 'subtitle':'Recruitments done so far'}
    recruitments = Recruitments.query.filter_by(archived=0)
    result_dict = [u.name for u in recruitments]
    return jsonify(recruitments=result_dict)
  else:
    recruitments = Recruitments(name=request.form.get('name'))
    db.session.add(recruitments)
    db.session.commit()
    return jsonify(status='ok')

@api.route('/recruitment/<int:id>', methods=['GET', 'POST'])
def api_recruitment(id):
  if request.method == 'GET':
    page={'title':'Recruitments', 'subtitle':'Recruitments done so far'}
    recruitment = Recruitments.query.filter_by(id=id).first()
    return jsonify({'name':recruitment.name, 'id':recruitment.id})
  else:
    recruitments = Recruitments(name=request.form.get('name'))
    db.session.add(recruitments)
    db.session.commit()
    return jsonify(status='ok')

@api.route('/users/json', methods=['GET'])
def api_users():
  users = User.query.all()
  api_data = []
  for user in users:
    api_data.append({'id':user.id, 'name':user.name, 'country':user.location, 'username': user.username, 'app_name': user.app_name, 'email': user.email})
  return jsonify(users=api_data)

@api.route('/test/json', methods=['GET', 'POST'])
def get_test_url():
  if request.method == 'GET':
    return jsonify(status='get')
  else:
    return jsonify(status='post')

@api.route('/sync/recruitments', methods=['GET', 'POST'])
def sync_recruitments():
  if request.method == 'GET':
    records  = Recruitments.query.filter(Recruitments.archived != 1)
    return jsonify({'recruitments':[record.to_json() for record in records]})
  else:
    status = []
    recruitment_list = request.json.get('recruitments')
    for recruitment in recruitment_list:
      record = Recruitments.from_json(recruitment)
      #exists = db.session.query(db.exists().where(User.name == 'davidism')).scalar()
      if not db.session.query(db.exists().where(Recruitments.id == record.id)).scalar():
         db.session.add(record)
      # else:
      #   db.session.commit()
      status.append({'id':record.id, 'status':'ok'})
    return jsonify(status=status)

@api.route('/sync/registrations', methods=['GET', 'POST'])
def sync_registrations():
  if request.method == 'GET':
    records  = Registration.query.filter(Registration.archived != 1)
    return jsonify({'registrations':[record.to_json() for record in records]})
  else:
    status = []
    registration_list = request.json.get('registrations')
    for registration in registration_list:
      record = Registration.from_json(registration)
      #exists = db.session.query(db.exists().where(User.name == 'davidism')).scalar()
      if not db.session.query(db.exists().where(Registration.id == record.id)).scalar():
         db.session.add(record)
      # else:
      #   db.session.commit()
      status.append({'id':record.id, 'status':'ok'})
    return jsonify(status=status)

@api.route('/sync/interviews', methods=['GET', 'POST'])
def sync_interviews():
  if request.method == 'GET':
    records  = Interview.query.filter(Interview.archived != 1)
    return jsonify({'interviews':[record.to_json() for record in records]})
  else:
    status = []
    interview_list = request.json.get('interviews')
    for interview in interview_list:
      record = Interview.from_json(interview)
      #exists = db.session.query(db.exists().where(User.name == 'davidism')).scalar()
      if not db.session.query(db.exists().where(Interview.id == record.id)).scalar():
         db.session.add(record)
      # else:
      #   db.session.commit()
      status.append({'id':record.id, 'status':'ok'})
    return jsonify(status=status)


@api.route('/sync/exams', methods=['GET', 'POST'])
def sync_exams():
  if request.method == 'GET':
    records  = Exam.query.filter(Exam.archived != 1)
    return jsonify({'exams':[record.to_json() for record in records]})
  else:
    status = []
    exam_list = request.json.get('exams')
    for exam in exam_list:
      record = Exam.from_json(exam)
      #exists = db.session.query(db.exists().where(User.name == 'davidism')).scalar()
      if not db.session.query(db.exists().where(Exam.id == record.id)).scalar():
         db.session.add(record)
      # else:
      #   db.session.commit()
      status.append({'id':record.id, 'status':'ok'})
    return jsonify(status=status)

