from flask import (render_template, redirect, url_for, flash, request, abort,
                   current_app, jsonify, make_response)
from flask_login import current_user, login_required
from flask.ext import excel
from sqlalchemy import func, distinct, select, and_
from . import main
from .. import db
from .forms import (EditProfileForm, EditProfileAdminForm, TrainingVenueForm, TrainingForm,
                    DeleteTrainingForm, TrainingClassForm, TrainingSessionForm, SessionTopicForm, SessionTypeForm)
from ..models import (Permission, Role, User, Geo, UserType, Mapping, LocationTargets, Exam, Village, Ward,
                      Location, Education, EducationLevel, Referral, Parish, SubCounty, Recruitments, Registration,
                      Interview, Branch, Cohort, RecruitmentUsers, LinkFacility, CommunityUnit, Training,
                      TrainingClasses, TrainingSession, SessionAttendance, TrainingVenues, Trainees, SessionTopic,
                      TrainingSessionType)
from ..decorators import admin_required, permission_required
from flask_googlemaps import Map, icons
from datetime import date, datetime, time
from time import gmtime, strftime
import os, time, calendar, uuid
from ..data import data
import io
import csv
import operator

currency = 'UGX '

# @main.route('/main', methods=['GET', 'POST'])
# def index_main():
#     if current_user.is_anonymous():
#         return redirect(url_for('auth.login'))
#     else:
#         return jsonify(id=current_user.id)


@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
    page = {'title': 'Home'}
    total_registrations = Registration.query.filter_by(archived=0)
    registrations = total_registrations.count()

    total_mappings = Mapping.query.filter_by(archived=0).order_by(Mapping.client_time.desc())
    mapping = total_mappings.count()
    mappings = total_mappings.limit(5).all()
    total_recruitments = Recruitments.query.filter_by(archived=0)
    recruitments = total_recruitments.count()
    
    trainings = Training.query.filter_by(archived=0).limit(current_app.config['FOLLOWERS_PER_PAGE']).all()
    recruitment = Recruitments.query.filter_by(archived=0).limit(current_app.config['FOLLOWERS_PER_PAGE']).all()

    villages = Village.query.filter_by(archived=0).count()
    if current_user.is_anonymous():
        return redirect(url_for('auth.login'))
    else:
        return render_template('index.html', page=page, registrations=registrations, mapping=mapping, mappings=mappings,
                               recruitments=recruitments, villages=villages, currency=currency, trainings= trainings,
                               recruitment=recruitment)


@main.route('/registration/<string:id>', methods=['GET', 'POST'])
@login_required
def application_details(id):
    if request.method == 'GET':
        a = Registration.query.filter_by(id=id).first_or_404()
        mytime = time.strftime('%Y-%m-%d', time.localtime(1347517370))
        dob = time.strftime('%Y-%m-%d', time.localtime(a.dob / 1000))
        birthdate = datetime.strptime(dob, '%Y-%m-%d')
        age = ((datetime.today() - birthdate).days/365)
        page = {'title':a.name, 'subtitle':'Registration details'}
        # age = time.time() - float(a.dob)
        qualified = a.dob
        interview = Interview.query.filter_by(applicant=id).first()
        exam = Exam.query.filter_by(applicant=id).first()
        return render_template('registration.html', exam=exam, dob=dob,
            page=page, interview=interview, registration=a, age=age)


@main.route('/trainings', methods=['GET', 'POST'])
@login_required
def trainings():
  trainings = Training.query.filter_by(archived=0)
  page = {'title': 'Trainings', 'subtitle': 'All trainings'}
  return render_template(
      'trainings.html',
      trainings=trainings,
      page=page
    )


@main.route('/trainings/new', methods=['GET', 'POST'])
@login_required
def new_training():
  training_map = Map(
    identifier="map",
    lat=-1.2728,
    lng=36.7901,
    zoom=8,
    markers=[
      {
        'icon': 'http://maps.google.com/mapfiles/ms/icons/red-dot.png',
        'lat': -1.2728,
        'lng': 36.7901
      }
    ]
  )
  form = TrainingForm()
  if form.validate_on_submit():
    commenced_date = form.date_commenced.data
    completed_date = form.date_completed.data
    pattern = '%Y-%m-%d'
    commenced_epoch = int(time.mktime(time.strptime(str(commenced_date), pattern)))
    completed_epoch = int(time.mktime(time.strptime(str(completed_date), pattern)))

    new_training = Training(
      id=uuid.uuid1(),
      training_name=form.training_name.data,
      country=Geo.query.filter_by(id=form.country.data).first().geo_code,
      county_id=form.county.data,
      location_id=form.location.data,
      subcounty_id=form.subcounty.data,
      ward_id=form.ward.data,
      district=form.district.data,
      recruitment_id=form.recruitment.data,
      parish_id=form.parish.data,
      lat=form.lat.data,
      lon=form.lon.data,
      training_venue_id=form.training_venue.data,
      training_status_id=form.training_status.data,
      client_time=int(time.time()),
      created_by=current_user.id,
      date_created=strftime("%Y-%m-%d %H:%M:%-S", gmtime()),
      archived=0,
      comment=form.comment.data,
      date_commenced=commenced_epoch,
      date_completed=completed_epoch
    )
    db.session.add(new_training)
    db.session.commit()
    return redirect('/trainings')
  return render_template(
    'form_training.html',
    training_map=training_map,
    form=form
  )


@main.route('/trainings/training_venues/new', methods=['GET', 'POST'])
@login_required
def new_training_venue():
  form = TrainingVenueForm()
  training_venue_map = Map(
    identifier="map",
    lat=-1.2728,
    lng=36.7901,
    zoom=8,
    markers=[
      {
        'icon': 'http://maps.google.com/mapfiles/ms/icons/red-dot.png',
        'lat': -1.2728,
        'lng': 36.7901
      }
    ]
  )

  if form.validate_on_submit():
    new_training_venue = TrainingVenues(
      id=uuid.uuid1(),
      name=form.name.data,
      mapping=form.mapping.data,
      lat=form.lat.data,
      lon=form.lon.data,
      inspected=form.inspected.data,
      country=form.country.data,
      selected=form.selected.data,
      capacity=form.capacity.data,
      date_added=strftime("%Y-%m-%d %H:%M:%-S", gmtime()),
      added_by=current_user.id,
      client_time=int(time.time()),
      meta_data='{}',
      archived=form.archived.data
    )
    db.session.add(new_training_venue)
    db.session.commit()
    return redirect('/trainings')
  return render_template(
    'form_training_venue.html',
    form=form,
    training_venue_map=training_venue_map
  )


@main.route('/training/<string:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_training(id):
  training = Training.query.filter_by(id=id).first_or_404()
  form = TrainingForm()
  if form.validate_on_submit():
    training.training_name = form.training_name.data
    training.country = Geo.query.filter_by(id=form.country.data).first().geo_code
    training.county_id = form.county.data if training.country == 'KE' else None
    training.location_id = form.location.data if training.country == 'UG' else None
    training.subcounty_id = form.subcounty.data if training.country == 'KE' else None
    training.ward_id = form.ward.data if training.country == 'KE' else None
    training.district = form.district.data if training.country == 'UG' else None
    training.recruitment_id = form.recruitment.data if form.recruitment.data != '' else None
    training.parish_id = form.parish.data if training.country == 'UG' else None
    training.lat = form.lat.data
    training.lon = form.lon.data
    training.training_venue_id = None if form.training_venue.data == '-1' else form.training_venue.data
    training.training_status_id = None if form.training_status.data == -1 else form.training_status.data
    training.archived = 0
    training.comment = form.comment.data
    training.date_commenced = (datetime.combine(form.date_commenced.data, datetime.min.time()) -
                               datetime.utcfromtimestamp(0)).total_seconds() * 1000.0
    training.date_completed = (datetime.combine(form.date_completed.data, datetime.min.time()) -
                               datetime.utcfromtimestamp(0)).total_seconds() * 1000.0
    db.session.add(training)
    db.session.commit()
    return redirect(url_for('main.trainings'))
  form.training_name.data = training.training_name
  form.country.data = Geo.query.filter_by(geo_code=training.country).first().id
  form.county.data = training.county
  form.location.data = training.location
  form.subcounty.data = training.subcounty
  form.ward.data = training.ward
  form.district.data = training.district
  form.recruitment.data = training.recruitment
  form.parish.data = training.parish
  form.lat.data = training.lat
  form.lon.data = training.lon
  form.training_venue.data = training.training_venue_id
  form.training_status.data = training.training_status_id
  form.comment.data = training.comment
  form.date_commenced.data = datetime.fromtimestamp(training.date_commenced/1000) if training.date_commenced is not None else None
  form.date_completed.data = datetime.fromtimestamp(training.date_completed/1000) if training.date_completed is not None else None
  return render_template(
      'edit_training.html',
      form=form,
      training=training
    )


@main.route('/training/<string:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_training(id):
  training = Training.query.filter_by(id=id).first_or_404()
  form = DeleteTrainingForm()
  if form.validate_on_submit():
    db.session.delete(training)
    db.session.commit()
    return redirect('/trainings')
  return render_template(
    'form_delete_training.html',
    form=form,
    training_id=training.id
  )


@main.route('/training/<string:id>', methods=['GET', 'POST'])
@login_required
def training(id):
  training = Training.query.filter_by(id=id).first_or_404()
  page = {'title': training.training_name,
          'subtitle': '{training} training details'\
                      .format(training=training.training_name)
          }
  return render_template(
      'training.html',
      training=training,
      page=page
    )


@main.route('/training/<string:training_id>/sessions')
@login_required
def main_training_sessions(training_id):
  training = Training.query.filter_by(id=training_id).first_or_404()
  training_sessions = TrainingSession.query.filter_by(training_id=training_id)
  page = {'title': 'Sessions',
          'subtitle': 'Sessions in the {training} training'
            .format(training=training.training_name)}
  return render_template(
    'training_sessions.html',
    training=training,
    training_sessions=training_sessions,
    page=page
  )


@main.route('/training/<string:training_id>/attendance')
@login_required
def main_training_attendance(training_id):
  training = Training.query.filter_by(id=training_id).first_or_404()
  training_attendance = SessionAttendance.query.filter_by(training_id=training_id)
  page = {'title': 'Classes',
          'subtitle': 'Classes in the {training} training'
            .format(training=training.training_name)}
  return render_template(
    'training_attendance.html',
    training_attendance=training_attendance,
    page=page,
    training=training
  )


@main.route('/training/<string:training_id>/classes', methods=['GET', 'POST'])
@login_required
def training_classes(training_id):
  training = Training.query.filter_by(id=training_id).first_or_404()
  training_classes = TrainingClasses.query.filter_by(training_id=training_id)
  page = {'title': 'Classes',
          'subtitle':'Classes in the {training} training'
          .format(training=training.training_name)}
  return render_template(
    'training_classes.html',
    training_classes=training_classes,
    page=page,
    training=training
  )


@main.route('/training/<string:training_id>/classes/new', methods=['GET', 'POST'])
@login_required
def new_training_class(training_id):
  training = Training.query.filter_by(id=training_id).first_or_404()
  form = TrainingClassForm()
  page = {'title': 'New Class'}
  if form.validate_on_submit():
    training_classes_ids = [
      t_classes_id[0] for t_classes_id in TrainingClasses.query.with_entities(TrainingClasses.id)
    ]
    if len(max(training_classes_ids)) == 0:
      new_id = 0
    else:
      new_id = max(training_classes_ids)+1
    new_class = TrainingClasses(
      id=new_id,  # ask how int ids are generated
      training_id=training.id,
      class_name=form.class_name.data,
      created_by=current_user.id,
      client_time=int(time.time()),
      date_created=strftime("%Y-%m-%d %H:%M:%S", gmtime()),
      archived=form.archived.data,
      country=Geo.query.filter_by(id=form.country.data).first().geo_code
    )
    db.session.add(new_class)
    db.session.commit()
    return redirect('/training/' + str(training.id) + '/classes')
  return render_template(
    'form_training_class.html',
    page=page,
    form=form,
    training=training
  )


@main.route('/training/<string:training_id>/classes/<string:class_id>/edit_class', methods=['GET', 'POST'])
@login_required
def edit_training_class(training_id, class_id):
  training = Training.query.filter_by(id=training_id).first_or_404()
  training_class = TrainingClasses.query.filter_by(id=class_id).first_or_404()
  form = TrainingClassForm()
  page = {
    'title': 'Edit class'
  }
  if form.validate_on_submit():
    training_class.class_name = form.class_name.data
    training_class.country = Geo.query.filter_by(id=form.country.data).first().geo_code
    training_class.archived = form.archived.data
    db.session.add(training_class)
    db.session.commit()
  form.class_name.data = training_class.class_name
  form.country.data = Geo.query.filter_by(geo_code=training.country).first().id
  form.archived.data = training_class.archived
  return render_template(
    'edit_training_class.html',
    training_class=training_class,
    page=page,
    form=form
  )


@main.route('/training/<string:training_id>/classes/<string:class_id>/delete_class')
@login_required
def delete_training_class(training_id, class_id):
  training = Training.query.filter_by(id=training_id).first_or_404()
  training_class = TrainingClasses.query.filter_by(id=class_id).first_or_404()
  form = DeleteTrainingForm()
  page = {
    'title': 'Delete class'
  }
  if form.validate_on_submit():
    db.session.delete(training_class)
    db.session.commit()
    return redirect('/training/' + str(training.id) + '/classes/' + str(training_class.id) + '/class')
  return render_template(
    'form_delete_training_class.html',
    training_class=training_class,
    form=form,
    page=page
  )


@main.route('/training/<string:training_id>/classes/<string:class_id>')
@login_required
def training_class(training_id, class_id):
  training = Training.query.filter_by(id=training_id).first_or_404()
  training_class = TrainingClasses.query.filter_by(id=class_id).first_or_404()
  page = {
    'title': '{training_class} class'.format(training_class=training_class.class_name),
    'subtitle': 'Sessions in the {training_class} class'.format(training_class=training_class.class_name)
  }
  return render_template(
    'training_class.html',
    training_class=training_class,
    page=page,
    training=training
  )


@main.route('/training/<string:training_id>/classes/<string:class_id>/class_attendance')
@login_required
def training_class_attendance(training_id, class_id):
  training = Training.query.filter_by(id=training_id).first_or_404()
  training_class = TrainingClasses.query.filter_by(id=class_id).first_or_404()
  training_class_attendance = SessionAttendance.query.\
    join(SessionAttendance.training_session, aliased=True).\
    filter_by(class_id=class_id)
  page = {
    'title': '{training_class} class'.format(training_class=training_class.class_name),
    'subtitle': 'Sessions in the {training_class} class'.format(training_class=training_class.class_name)
  }
  return render_template(
    'training_class_attendance.html',
    training_class=training_class,
    training_class_attendance=training_class_attendance,
    page=page,
    training=training
  )


@main.route('/training/<string:training_id>/classes/<string:class_id>/class_sessions')
@login_required
def training_sessions(training_id, class_id):
  training = Training.query.filter_by(id=training_id).first_or_404()
  training_class = TrainingClasses.query.filter_by(id=class_id).first_or_404()
  training_class_sessions = TrainingSession.query.filter_by(class_id=class_id)
  page = {
    'title': '{training_class} class'.format(training_class=training_class.class_name),
    'subtitle': 'Sessions in the {training_class} class'.format(training_class=training_class.class_name)
  }
  return render_template(
    'training_class_sessions.html',
    training_class=training_class,
    training_class_sessions=training_class_sessions,
    page=page,
    training=training
  )


@main.route('/training/<string:training_id>/classes/<string:class_id>/class_sessions/new', methods=['GET', 'POST'])
@login_required
def new_training_sessions(training_id, class_id):
  training = Training.query.filter_by(id=training_id).first_or_404()
  training_class = TrainingClasses.query.filter_by(id=class_id).first_or_404()
  form = TrainingSessionForm()
  page = {
    'title': '{training_class} class'.format(training_class=training_class.class_name),
    'subtitle': 'Sessions in the {training_class} class'.format(training_class=training_class.class_name)
  }
  if form.validate_on_submit():
    new_session = TrainingSession(
      id=uuid.uuid1(),
      training_session_type_id=form.training_session_type.data,
      class_id=training_class.id,
      training_id=training.id,
      trainer_id=form.trainer.data,
      country=Geo.query.filter_by(id=form.country.data).first().geo_code,
      archived=form.archived.data,
      comment=form.comment.data,
      session_start_time=0,
      session_end_time=0,
      session_topic_id=form.session_topic.data,
      session_lead_trainer=form.session_lead_trainer.data,
      client_time=int(time.time()),
      created_by=current_user.id,
      date_created=strftime("%Y-%m-%d %H:%M:%S", gmtime())
    )
    db.session.add(new_session)
    db.session.commit()
    return redirect('/training/' + str(training.id) + '/classes/' + str(training_class.id) + '/class_sessions')
  return render_template(
    'form_training_class_session.html',
    training_class=training_class,
    form=form,
    page=page,
    training=training
  )


@main.route('/training/<string:training_id>/classes/<string:class_id>/class_sessions/<string:session_id>/edit',
            methods=['GET', 'POST'])
@login_required
def edit_training_sessions(training_id, class_id, session_id):
  training = Training.query.filter_by(id=training_id).first_or_404()
  training_class = TrainingClasses.query.filter_by(id=class_id).first_or_404()
  training_class_session = TrainingSession.query.filter_by(id=session_id).first_or_404()
  page = {
    'title': 'Edit session'
  }
  form = TrainingSessionForm()
  if form.validate_on_submit():
    training_class_session.training_session_type_id = form.training_session_type.data
    training_class_session.country = Geo.query.filter_by(id=form.country.data).first().geo_code
    training_class_session.trainer_id = form.trainer.data
    training_class_session.archived = form.archived.data
    training_class_session.comment = form.comment.data
    training_class_session.session_topic_id = form.session_topic.data
    training_class_session.session_lead_trainer = form.session_lead_trainer.data
    db.session.add(training_class_session)
    db.session.commit()
    return redirect('/training/' + training_id + '/classes/' + class_id + '/class_sessions')
  form.training_session_type.data = training_class_session.training_session_type_id
  form.trainer.data = training_class_session.trainer_id
  form.archived.data = training_class_session.archived
  form.comment.data = training_class_session.comment
  form.session_topic.data = training_class_session.session_topic_id
  form.session_lead_trainer.data = training_class_session.session_lead_trainer
  return render_template(
    'edit_training_session.html',
    training_class=training_class,
    training_session=training_class_session,
    form=form,
    training=training
  )


@main.route('/training/<string:training_id>/classes/<string:class_id>/class_sessions/<string:session_id>/delete',
            methods=['GET', 'POST'])
@login_required
def delete_training_sessions(training_id, class_id, session_id):
  training = Training.query.filter_by(id=training_id).first_or_404()
  training_class = TrainingClasses.query.filter_by(id=class_id).first_or_404()
  training_class_session = TrainingSession.query.filter_by(id=session_id).first_or_404()
  page = {
    'title': 'Delete session'
  }
  form = DeleteTrainingForm()
  if form.validate_on_submit():
    db.session.delete(training_class_session)
    db.session.commit()
    return redirect('/training/' + training_id + '/classes/' + class_id + '/class_sessions')
  return render_template(
    'form_delete_training_session.html',
    training_class=training_class,
    training_session=training_class_session,
    form=form,
    training=training
  )


@main.route('/training/<string:training_id>/<string:class_id>/new_session_topic', methods=['GET', 'POST'])
@login_required
def new_session_topic(training_id, class_id):
  form = SessionTopicForm()
  if form.validate_on_submit():
    session_topic_ids = [
      sess_t_id[0] for sess_t_id in SessionTopic.query.with_entities(SessionTopic.id)
    ]
    if len(max(session_topic_ids)) == 0:
      new_id = 0
    else:
      new_id = max(session_topic_ids)+1
    new_topic = SessionTopic(
      id=new_id,
      name=form.name.data,
      country=Geo.query.filter_by(id=form.country.data).first().geo_code,
      archived=form.archived.data,
      date_added=strftime("%Y-%m-%d %H:%M:%S", gmtime()),
      added_by=current_user.id
    )
    db.session.add(new_topic)
    db.session.commit()
    return redirect('/training/' + training_id + '/classes/' + class_id + '/class_sessions')
  return render_template(
    'form_session_topic.html',
    form=form
  )


@main.route('/training/<string:training_id>/<string:class_id>/new_session_type', methods=['GET', 'POST'])
@login_required
def new_session_type(training_id, class_id):
  form = SessionTypeForm()
  if form.validate_on_submit():
    training_session_type_ids = [
      t_sess_id[0] for t_sess_id in TrainingSessionType.query.with_entities(TrainingSessionType.id)
    ]
    if len(max(training_session_type_ids)) == 0:
      new_id = 0
    else:
      new_id = max(training_session_type_ids)+1
    new_type = TrainingSessionType(
      id=new_id,
      session_name=form.session_name.data,
      country=form.country.data,
      archived=form.archived.data,
      client_time=int(time.time()),
      date_created=strftime("%Y-%m-%d %H:%M:%S", gmtime()),
      created_by=current_user.id
    )
    db.session.add(new_type)
    db.session.commit()
    return render_template('/training/' + training_id + '/classes/' + class_id + '/class_sessions')
  return render_template(
    'form_session_type.html',
    form=form
  )


@main.route('/training/<string:training_id>/classes/<string:class_id>/class_sessions/<string:session_id>',
            methods=['GET', 'POST'])
@login_required
def training_attendance(training_id, class_id, session_id):
  training = Training.query.filter_by(id=training_id).first_or_404()
  training_class = TrainingClasses.query.filter_by(id=class_id).first_or_404()
  training_session = TrainingSession.query.filter_by(id=session_id).first_or_404()
  training_attendance = SessionAttendance.query.filter_by(training_session_id=session_id)
  page = {'title': 'Attendance',
          'subtitle': 'Attendance for the {training_session} session'
          .format(
            training_session=training_session.date_created
            )
          }
  return render_template(
    'training_class_session.html',
    training_attendance=training_attendance,
    training=training,
    training_class=training_class,
    training_session=training_session,
    page=page
  )


@main.route('/training/<string:id>/trainees', methods=['GET', 'POST'])
@login_required
def training_trainees():
  training = Training.query.filter_by(id=id).first_or_404()
  training_trainees = Trainees.query.filter_by(training_id=id)
  page = {'title': 'Trainees', 'subtitle':'Trainees in the {training} training'.format(training=training.name)}
  return render_template(
      'training_trainees.html',
      page=page,
      training_trainees=training_trainees
    )


@main.route('/training/<string:id>/trainers', methods=['GET', 'POST'])
@login_required
def training_trainers(id):
  training = Training.query.filter_by(id=id).first_or_404()
  training_trainers = 'Training\'s Trainers'
  page = {'title': 'Trainers', 'subtitle':'Trainers in the {training} training'.format(training=training.name)}
  return render_template(
      'training_trainers.html',
      training_trainers=training_trainers
    )

@main.route('/mapping/<string:id>/download', methods=['GET', 'POST'])
@login_required
def mapping_village_data(id):
  if request.method == 'GET':
    villages = Village.query.filter_by(mapping_id=id)
    map_details = Mapping.query.filter_by(id=id).first()
    dest = io.StringIO()
    writer=csv.writer(dest)
    csv_data=[]
    header = [
        "District",
        "County",
        "Subcounty",
        "Parish",
        "Village/zone/cell",
        "Village Ranking",
        "Index Sum",
        "CHPs to recruit",
        "Cumulative CHPs",
        "LC Name",
        "LC Contact Number (don't use leading 0)",
        "Visit Completed By",
        "Visit Date",
        "GPS Lat",
        "GPS Lon",
        "Distance to branch",
        "Distance to branch index",
        "Est cost of transport to branch",
        "Est cost of transport to branch index",
        "Distance to main road",
        "Distance to main road index",
        "Number of HH",
        "Number of HH index",
        "Est population density",
        "Est population density index",
        "Area economic status",
        "Area economic status index",
        "Distance to nearest health facility",
        "Distance to nearest health facility index",
        "Stock level for ACT",
        "Stock level for ACT index",
        "Cost of ACT",
        "Cost of ACT index",
        "Presence of estates",
        "Presence of estates index",
        "Presence of factories",
        "Presence of factories index",
        "Presence of universities",
        "Presence of universities index",
        "Presence of distributors",
        "Presence of distributors index",
        "Presence trader market",
        "Presence trader market index",
        "Presence large super market",
        "Presence large super market index",
        "Presence of NGO distributing free drugs",
        "Presence of NGO distributing free drugs index",
        "Is BRAC CHP operating in this area?",
        "BRAC index",
        "Presence of other NGOs with any connection with LG/ Any other NGOs with ICCM programs?",
        "Presence of other NGOs with any connection with LG index",
        "1. Which ones?",
        "2. Which ones?",
        "MTN connectivity",
        "MTN connectivity index",
        "Comments (summarize)	"
        ]
    cumulative_chps=0
    ranks = []
    for village in villages:
      mapping = village.mapping
      subcounty = Location.query.filter_by(id=mapping.subcounty).first()
      county = subcounty.parent1
      district=county.parent1
      cumulative_chps =village.chps_to_recruit() + cumulative_chps
      ranks.append(village.village_index_score())
      rowdata=[
        district.name,
        county.name,
        subcounty.name,
        village.parish.name,
        village.village_name,
        "Ranking not found",
        village.village_index_score(),
        village.chps_to_recruit(),
        cumulative_chps,
        village.area_chief_name,
        village.area_chief_phone,
        village.user.name,
        datetime.fromtimestamp(village.client_time/1000).strftime('%Y-%m-%d %H:%M:%S'),
        village.lat,
        village.lon,
        village.distancetobranch,
        str(village.distance_to_branch_score()),
        village.transportcost,
        village.est_cost_of_transport_score(),
        village.distancetomainroad,
        village.distance_to_main_road_score(),
        village.noofhouseholds,
        village.number_of_hh_score(),
        village.estimatedpopulationdensity,
        village.number_of_hh_score(),
        village.economic_status,
        village.area_economic_status_score(),
        village.distancetonearesthealthfacility,
        village.distance_to_health_facility_score(),
        village.actlevels,
        village.stock_level_for_act_score(),
        village.actprice,
        village.cost_of_act_score(),
        village.presenceofestates,
        village.presence_of_estates_score(),
        village.number_of_factories,
        village.presence_of_factories_score(),
        village.presenceofhostels,
        village.presence_of_universities_score(),
        village.presenceofdistibutors,
        village.presence_of_distributors_score(),
        village.tradermarket,
        village.presence_trader_market_score(),
        village.largesupermarket,
        village.presence_large_supermarket_score(),
        village.ngosgivingfreedrugs,
        village.presence_of_ngo_distributing_free_drugs_score(),
        village.brac_operating,
        "",
        village.ngodoingiccm,
        village.presence_of_partner_ngos_score(),
        village.nameofngodoingiccm,
        village.nameofngodoingmhealth,
        village.mtn_signal,
        village.mtn_connectivity_score(),
        village.comment
      ]
      csv_data.append(rowdata)
    ranks.sort(reverse=True)
    pos = 1
    village_rank={}
    for rank in ranks:
      if not village_rank.has_key(rank):
        village_rank[rank]=pos
        pos+=1
    
    csv_data.sort(key=operator.itemgetter(6), reverse=True) # now sorted

    i=0
    for d in csv_data:
      csv_data[i][5] = village_rank.get(csv_data[i][6])
      i+=1
    csv_data.insert(0, header)
    output = excel.make_response_from_array(csv_data, 'csv')
    output.headers["Content-Disposition"] = "attachment; filename="+map_details.name+"-Village-Mapping-tool.csv"
    output.headers["Content-type"] = "text/csv"
    return output
      


@main.route('/export-scoring-tool/<string:id>', methods=['GET'])
@login_required
def export_scoring_tool(id):
    # get the registrations for the recruitment
    # Define our CSV
    dest = io.StringIO()
    writer = csv.writer(dest)
    data = []
    recruitment = Recruitments.query.filter_by(id=id).first_or_404()
    if recruitment.country == 'KE':
        header = [
            'CHEW Name',
            'CHEW Contact',
            'Candidate Name',
            'Candidate Mobile',
            'Gender',
            'Year of Birth',
            'Age',
            'Subcounty',
            'Ward',
            'Village/zone/cell',
            'Landmark',
            'CU (Community Unit)',
            'Link Facility',
            'No of Households',
            'Read/speak English',
            'Years at this Location',
            'Other Languages',
            'CHV',
            'GOK Training',
            'Other Trainings',
            'Highest education level',
            'Previous/Current health or business experience',
            'Community group membership',
            'Financial Accounts',
            'Recruitment Comments',
            'Math Score',
            'Reading Comprehension',
            'About you',
            'Total Score',
            'Eligible for Interview',
            'Interview: Overall Motivation',
            'Interview: Ability to work with communities',
            'Interview: Mentality',
            'Interview:Selling skills',
            'Interview: Interest in health',
            'Interview: Ability to invest',
            'Interview: Interpersonal skills',
            'Interview: Ability to commit',
            'Interview Score',
            'DO NOT ASK OUTLOUD: Any conditions to prevent joining?',
            'Tranport as Per Recruitment',
            'Comments',
            'Qualify for Training',
            'Completed By',
            'Invite for Training']
        data.append(header)
        registrations = Registration.query.filter(Registration.recruitment == id)
        for registration in registrations:
            # metadata for registration include:
            # Exam, Interview, Chew, Recruitment, Link Facility, subcounty, education, added, by, referral, ward
            # Get Exam
            
            exam = Exam.query.filter(Exam.applicant == registration.id).first()
            interview = Interview.query.filter(Interview.applicant == registration.id).first()
            if registration.referral_id is not None and registration.referral_id != '':
                chew = Referral.query.filter_by(id=registration.referral_id).first()
            else:
                chew = Referral.query.filter_by(id='0').first()
            link_facility = LinkFacility.query.filter_by(id=registration.link_facility).first()
            subcounty = SubCounty.query.filter_by(id=registration.subcounty).first()
            education = Education.query.filter_by(id=registration.education).first()
            ward = Ward.query.filter_by(id=registration.ward).first()
            community_unit = CommunityUnit.query.filter_by(id=registration.cu_name).first()
            
            math = 0
            english = 0
            personality = 0
            exam_total = 0
            exam_passed = "N"
            if exam:
                if exam.math == 0 or exam.english == 0 or exam.personality == 0:
                    exam_passed= "N"
                elif exam.total_score() < 10:
                    exam_passed = "N"
                else:
                    exam_passed = "Y"
                exam_total = exam.total_score()
                math = exam.math
                english = exam.english
                personality = exam.personality
                
            user = ""
            motivation = 0
            community = 0
            mentality = 0
            selling = 0
            health = 0
            investment = '0'
            interpersonal = '0'
            commitment = 0
            total_score = 0
            canjoin = "N"
            qualified = "N"
            comment = ""
            selected = ""
    
            if interview:
                user = str(interview.user.name)
                motivation = interview.motivation
                community = interview.community
                mentality = interview.mentality
                selling = interview.selling
                health = interview.health
                investment = str(interview.investment)
                interpersonal = str(interview.interpersonal)
                commitment = interview.commitment
                total_score = interview.total_score()
                qualified = 'Y' if interview.has_passed and exam_passed == 'Y' else 'N'
                if total_score > 24 and interview.canjoin == 1 and exam_passed == 'Y':
                    qualified = 'Y'
                else:
                    qualified ='N'
                canjoin = 'Y' if interview.canjoin == 1 else 'N'
                comment = interview.comment.replace(',', ';')
                if interview.selected ==1:
                  selected = 'Y'
                elif interview.selected == 2:
                  selected='Waiting'
                else:
                  selected = 'N'
            # Now that we have what we need, we generate the CSV rows
            row = [
                chew.name if chew is not None else registration.chew_name,
                chew.phone if chew is not None else registration.chew_number,
                registration.name,
                registration.phone.replace(',', ':'),
                registration.gender,
                registration.date_of_birth(),
                registration.age(),
                subcounty.name if subcounty is not None else registration.subcounty,
                ward.name if ward is not None else registration.ward,
                registration.village.replace(',', ':'),
                registration.feature.replace(',', ':'),
                community_unit.name if community_unit is not None else registration.cu_name,
                link_facility.facility_name if link_facility is not None else registration.link_facility,
                str(registration.households),
                "Y" if registration.english == 1 else "N",
                registration.date_moved,
                registration.languages.replace(',', ';'),
                
                "Y" if registration.is_chv == 1 else "N",
                "Y" if registration.is_gok_trained == 1 else "N",
                registration.trainings.replace(',', ':'),
                education.name if education is not None else registration.education,
                registration.occupation,
                "Y" if registration.community_membership == 1 else "N",
                "Y" if registration.financial_accounts == 1 else "N",
                registration.comment.replace(',', ';'),
                math,
                english,
                personality,
                exam_total,
                exam_passed,
                str(motivation),
                str(community),
                str(mentality),
                str(selling),
                str(health),
                str(investment),
                str(interpersonal),
                str(commitment),
                str(total_score),
                str(canjoin),
                str(registration.recruitment_transport),
                str(comment),
                str(qualified),
                str(user),
                selected,
            ]
            data.append(row)
        
    else:
        registrations = Registration.query.filter(Registration.recruitment == id)
        header = [
            'Referral Name',
            'Referral Title',
            'Referral Mobile No',
            'VHT?',
            'Candidate Name',
            'Candidate Mobile',
            'Gender',
            'Age',
            'District',
            'Subcounty',
            'Parish',
            'Village/zone/cell',
            'Landmark',
            'Read/Speak English',
            'Other Languages',
            'Years at this location',
            'Ever worked with BRAC?',
            'If yes as BRAC CHP?',
            'Highest Educational',
            'Community group memberships',
            'Maths Score',
            'Reading comprehension',
            'About You',
            'Total Marks',
            'Eligible for Interview',
            'Interview Completed by,',
            'Interview: Overall Motivation',
            'Interview: Ability to work with communities',
            'Interview: Mentality',
            'Interview:Selling skills',
            'Interview: Interest in health',
            'Interview: Ability to invest',
            'Interview: Interpersonal skills',
            'Interview: Ability to commit',
            'Interview Score',
            'DO NOT ASK OUTLOUD: Any conditions to prevent joining?',
            'Comments',
            'Qualify for Training',
            'Invite for Training']
        data.append(header)
    
        for registration in registrations:
            # Get Exam
            exam = Exam.query.filter(Exam.applicant == registration.id).first()
            math = 0
            english = 0
            personality = 0
            exam_total = 0
            exam_passed = "N"
            if exam:
                math = exam.math
                english = exam.english
                personality = exam.personality
                exam_total = exam.total_score()
                exam_passed = "Y" if exam.has_passed() and registration.brac != 1 else "N"
    
            interview = Interview.query.filter(Interview.applicant == registration.id).first()
            user = ""
            motivation = 0
            community = 0
            mentality = 0
            selling = 0
            health = 0
            investment = '0'
            interpersonal = '0'
            commitment = 0
            total_score = 0
            canjoin = "N"
            qualified = "N"
            comment = ""
            canjoin = ""
            selected = ""
    
            if interview:
                user = str(interview.user.name)
                motivation = interview.motivation
                community = interview.community
                mentality = interview.mentality
                selling = interview.selling
                health = interview.health
                investment = str(interview.investment)
                interpersonal = str(interview.interpersonal)
                commitment = interview.commitment
                total_score = interview.total_score()
                qualified = 'Y' if interview.has_passed and exam_passed == 'Y' else 'N'
                canjoin = 'Y' if interview.canjoin == 1 else 'N'
                comment = interview.comment.replace(',', ';')
                canjoin = 'Y' if interview.canjoin == 1 else 'N'
                selected = 'Y' if interview.selected == 1 else 'N'  # if selected of not
            # interview= Interview.query.filter(Interview.archived != 1)
            # Now that we have what we need, we generate the CSV rows
            row = [
                registration.referral,
                registration.referral_title,
                registration.referral_number,
                "Y" if registration.vht == 1 else "N",
                registration.name,
                registration.phone.replace(',', ':'),
                registration.gender,
                registration.age(),
                registration.district,
                registration.subcounty,
                registration.parish,
                registration.village,
                registration.feature.replace(',', ':'),
                "Y" if registration.english == 1 else "N",
                registration.languages.replace(',', ';'),
                registration.date_moved,
                "Y" if registration.brac == 1 else "N",
                "Y" if registration.brac_chp == 1 else "N",
                registration.education,
                "Y" if registration.community_membership == 1 else "N",
                math,
                english,
                personality,
                exam_total,
                exam_passed,
                str(user),
                str(motivation),
                str(community),
                str(mentality),
                str(selling),
                str(health),
                str(investment),
                str(interpersonal),
                str(commitment),
                str(total_score),
                str(canjoin),
                str(comment),
                str(qualified),
                str(selected),
            ]
            data.append(row)
    output = excel.make_response_from_array(data, 'csv')
    output.headers["Content-Disposition"] = "attachment; filename=scoring-tool.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@main.route('/recruitments', methods=['GET', 'POST'])
@login_required
def recruitments():
  if request.method == 'GET':
    page={'title':'Recruitments', 'subtitle':'Recruitments done so far'}
    recruitments = Recruitments.query.filter_by(archived=0)
    return render_template('recruitments.html', recruitments=recruitments, currency=currency, page=page)
  else:
    # check if there is an iD or if the ID is blank
    if 'id' in request.form:
        recruitment = Recruitments.query.filter_by(id=request.form.get('id')).first()
        recruitment.name=request.form.get('name')
        db.session.commit()
        return jsonify(status='updated', id=recruitment.id)
    else:
        recruitments = Recruitments(name=request.form.get('name'), added_by=current_user.id)
        db.session.add(recruitments)
        db.session.commit()
        return jsonify(status='created', id=recruitments.id)

@main.route('/recruitment/<string:id>', methods=['GET', 'POST'])
@login_required
def recruitment(id):
  if request.method == 'GET':
    recruitment = Recruitments.query.filter_by(archived=0, id=id).first_or_404()
    registrations = Registration.query.filter_by(recruitment=id)
    page={'title':recruitment.name.title(), 'subtitle':recruitment.name if recruitment else 'Recruitments'}
    return render_template('recruitment.html', recruitment=recruitment, 
        registrations=registrations, page=page)
  else:
    if 'id' in request.form:
        recruitment = Recruitments.query.filter_by(id=request.form.get('id')).first()
        recruitment.name=request.form.get('name')
        db.session.commit()
        return jsonify(status='updated', id=recruitment.id)
    else:
        recruitments = Recruitments(name=request.form.get('name'), added_by=current_user.id)
        db.session.add(recruitments)
        db.session.commit()

        # also add the recruitment
        recruitment = RecruitmentUsers(user_id=current_user.id, recruitment_id= recruitments.id)
        return jsonify(status='created', id=recruitments.id)

@main.route('/country', methods=['GET', 'POST'])
@main.route('/region', methods=['GET', 'POST'])
@main.route('/county', methods=['GET', 'POST'])
@main.route('/district', methods=['GET', 'POST'])
@main.route('/sub-county', methods=['GET', 'POST'])
@main.route('/parish', methods=['GET', 'POST'])
@main.route('/ward', methods=['GET', 'POST'])
@main.route('/locations', methods=['GET', 'POST'])
@login_required
def create_location():
    # if request.method == 'POST':
    if request.method == 'POST':
        parent = request.form.get('parent')  if request.form.get('parent') != '0' else None
        location = Location(
            name = request.form.get('name').title(),
            parent = parent,
            lat = request.form.get('lat'),
            lon = request.form.get('lon'),
            admin_name = request.form.get('admin_name').title()
        )
        db.session.add(location)
        db.session.commit()
        return jsonify(status='ok', parent=parent)
    else:
        param = request.path.strip('/')
        all_locations = Location.query.all()
        if param is None or param == 'locations':
            locations = Location.query.all()
        else:
            locations = Location.query.filter_by(admin_name=param.title())
        page = {'title': param, 'subtitle': 'mapped '+param}
        inputmap = Map(
            identifier="view-side",
            lat=-1.2728,
            lng=36.7901,
            zoom=8,
            markers=[(-1.2728, 36.7901)]
        )
        return render_template('location.html', page=page, map=inputmap, currency=currency,
         all_locations=all_locations,  locations=locations)


@main.route('/villages', methods=['GET', 'POST'])
@login_required
def create_village():
    # if request.method == 'POST':
    if request.method == 'POST':
        pass
    else:
        page = {'title': 'Villages', 'subtitle': 'mapped Villages'}
        villages = Village.query.filter_by(archived=0)
        inputmap = Map(
            identifier="view-side",
            lat=-1.2728,
            lng=36.7901,
            zoom=8,
            markers=[(-1.2728, 36.7901)]
        )
        return render_template('villages.html', page=page, map=inputmap, currency=currency,
         villages=villages)


@main.route('/mappings', methods=['GET', 'POST'])
@login_required
def create_mappings():
    # if request.method == 'POST':
    if request.method == 'POST':
        pass
    else:
        page = {'title': 'Mappings', 'subtitle': ' Mappings'}
        mappings = Mapping.query.all()
        inputmap = Map(
            identifier="view-side",
            lat=-1.2728,
            lng=36.7901,
            zoom=8,
            markers=[(-1.2728, 36.7901)]
        )
        return render_template('mappings.html', page=page, map=inputmap, currency=currency,
         mappings=mappings)
    
    
@main.route('/mapping/<string:id>', methods=['GET', 'POST'])
@login_required
def get_mapping_data(id):
    # if request.method == 'POST':
    if request.method == 'POST':
        pass
    else:
        page = {'title': 'Mappings', 'subtitle': ' Mappings'}
        color = ['dark', 'grey', 'blue', 'green', 'red']
        mapping = Mapping.query.filter_by(id=id).first()
        parishes = Parish.query.filter_by(mapping_id=id)
        subcounties = SubCounty.query.filter_by(mappingId=id)
        villages = Village.query.filter_by(mapping_id=id)
        return render_template('mapping.html', page=page, villages=villages, mapping=mapping, parishes=parishes,
                               subcounties=subcounties, color=color)
    
    
@main.route('/branches', methods=['GET', 'POST'])
@login_required
def branches():
    if request.method == 'POST':
        branch = Branch(
            name = request.form.get('name').title(),
            location_id  = request.form.get('location_id'),
            lat = request.form.get('lat'),
            lon = request.form.get('lon')
        )
        db.session.add(branch)
        db.session.commit()
        return jsonify(status='ok', data=request.form)
    else:
        branches = Branch.query.all()
        branch_markers = []
        for record in branches:
            if record.lat != '' and record.lon != '':
                marker = {
                    'lat': record.lat,
                    'lng': record.lon,
                    'icon': icons.dots.blue,
                    'infobox': (
                        "<h2>"+record.name.title()+"</h2>"
                        "<br>200 New CHPs"
                        "<br><a href='village/"+str(record.id)+"'>More Details </a>"
                    )
                }
                branch_markers.append(marker)
        branch_maps = Map(
            identifier="branches",
            lat=-1.2728, # -1.272898, 36.790095
            lng=36.7901,
            zoom=8,
            style="height:500px;",
            markers=branch_markers,
            cluster = True,
            cluster_gridsize = 10
            )
        page = {'title': 'Branches', 'subtitle': 'List of branches'}
        
        locations = Location.query.all()
        return render_template('branches.html', branches=branches, currency=currency, clustermap=branch_maps, locations=locations, page=page)

@main.route('/cohort', methods=['GET', 'POST'])
@login_required
def cohort():
    if request.method == 'GET':
        page = {'title': 'Cohort', 'subtitle': 'List of all cohorts in all branches'}
        branches = Branch.query.all()
        cohorts = Cohort.query.all()
        return render_template('cohort.html', cohorts=cohorts, currency=currency, branches=branches, page=page)
    else:
        cohort = Cohort(
            cohort_number = request.form.get('name'),
            branch_id  = request.form.get('branch')
        )
        db.session.add(cohort)
        db.session.commit()
        return jsonify(status='ok', data=request.form)


@main.route('/get_location_expansion')
@login_required
def get_location_expansion():
  id = request.args.get('id')
  expansion = {}
  targets = LocationTargets.query.filter_by(location_id=id)
  for target in targets:
    expansion[time.mktime(date.datetime(target.recruitment.date_added))] = target.chps_needed
  return jsonify(expansion=expansion)



@main.route('/educations', methods=['GET', 'POST'])
@login_required
def educations():
    if request.method == 'GET':
        page = {'title': 'Education', 'subtitle': 'List of all education levels'}
        educations = Education.query.all()
        return render_template('educations.html', educations=educations, page=page, currency=currency)
    else:
        educations = Education(
            name = request.form.get('name')
        )
        db.session.add(educations)
        db.session.commit()
        return jsonify(status='ok', data=request.form)


@main.route('/education-level', methods=['GET', 'POST'])
@login_required
def education_levels():
    if request.method == 'GET':
        page = {'title': 'Education Level', 'subtitle': 'List of all education levels'}
        educations = Education.query.all()
        education_levels = EducationLevel.query.all()
        return render_template('education-level.html', education_levels=education_levels, educations=educations, page=page, currency=currency)
    else:
        educations = EducationLevel(
            level_name = request.form.get('name'),
            education_id = request.form.get('education')
        )
        db.session.add(educations)
        db.session.commit()
        return jsonify(status='ok', data=request.form)



@main.route('/refferals', methods=['GET', 'POST'])
@login_required
def refferals():
    if request.method == 'GET':
        page = {'title': 'Refferals', 'subtitle': 'List of persons who have reffered others'}
        refferals = Referral.query.all()
        locations = Location.query.all()
        return render_template('refferals.html', refferals=refferals, page=page, locations=locations, currency=currency)
    else:
        referral = Referral(
            name = request.form.get('name'),
            phone = request.form.get('phone'),
            title = request.form.get('title'),
            location_id = request.form.get('location')
        )
        db.session.add(referral)
        db.session.commit()
        return jsonify(status='ok', id=referral.id, data=request.form)

@main.route('/gmap-test')
def test_route():
    return render_template('gmap.html')

@main.route('/video-test')
def video_route():
    return render_template('video-bg.html')

@main.route('/user/<username>')
@login_required
def user(username):
    user = User.query.outerjoin(Geo).outerjoin(UserType)\
        .with_entities(User, Geo, UserType)\
        .filter(User.username==username).first_or_404()

    return render_template('user.html', user=user, vc_firms=[],
                           ai_firms=[], su_firms=[])


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        # change values based on form input
        geo = Geo.query.filter_by(id=form.geo.data).first()
        current_user.name = form.name.data
        current_user.location = geo.geo_code
        current_user.about_me = form.about_me.data
        current_user.geo = Geo.query.get(form.geo.data)
        current_user.user_type = UserType.query.get(form.user_type.data)
        db.session.add(current_user)
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.user', username=current_user.username))
    # set inital values
    form.name.data = current_user.name
    # form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    form.geo.data = current_user.geo_id
    form.user_type.data = current_user.user_type_id
    return render_template('edit_profile.html', form=form)




@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        username = form.email.data.split('@')[0]
        geo = Geo.query.filter_by(id=form.geo.data).first()
        user.email = form.email.data
        user.username = username
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = geo.geo_code
        user.geo = Geo.query.get(form.geo.data)
        user.user_type = UserType.query.get(form.user_type.data)
        user.about_me = form.about_me.data
        if (form.edit_password.data):
            user.password = form.password.data
            user.app_name = form.password.data.encode('base64'),
        db.session.add(user)
        flash('The profile has been updated.', 'success')
        return redirect(url_for('main.user', username=user.username))
    form.email.data = user.email
    # form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    # form.location.data = user.location
    form.geo.data = user.geo_id
    form.user_type.data = user.user_type_id
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


# @main.route('/post/<int:id>')
# @login_required
# def post(id):
#     post = Post.query.get_or_404(id)
#     return render_template('post.html', posts=[post])
#
#
# @main.route('/edit/<int:id>', methods=['GET', 'POST'])
# @login_required
# def edit(id):
#     post = Post.query.get_or_404(id)
#     if current_user != post.author and \
#             not current_user.can(Permission.ADMINISTER):
#         abort(403)
#     form = PostForm()
#     if form.validate_on_submit():
#         post.body = form.body.data
#         db.session.add(post)
#         flash('The post has been updated.', 'success')
#         return redirect(url_for('main.post', id=post.id))
#     form.body.data = post.body
#     return render_template('edit_post.html', form=form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.', 'error')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash('You are already following this user.', 'error')
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username, 'success')
    return redirect(url_for('main.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.', 'error')
        return redirect(url_for('main.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.', 'error')
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    flash('You are not following %s anymore.' % username, 'success')
    return redirect(url_for('main.user', username=username))


@main.route('/followers/<username>')
@login_required
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.', 'error')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='main.followers', pagination=pagination,
                           follows=follows)

@main.route('/followed-by/<username>')
@login_required
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='main.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/csv')
def test_app():
  with open('data.csv', 'r') as f:
    data_numbers = {}
    districts = {}
    counties = {}
    sub_counties = {}
    for row in csv.reader(f.read().splitlines()):
      data_numbers[row[3]]= {'county':row[2], 'district':row[1], 'number':row[0]}
      if row[1] in districts:
        if row[2] in districts.get(row[1]):
          districts[row[1]][row[2]].append({'name':row[0], 'number':row[3]})
        else:
          districts[row[1]][row[2]] = []
          districts[row[1]][row[2]].append({'name':row[0], 'number':row[3]})
      else:
        districts[row[1]] = {}
        districts[row[1]][row[2]] = []
        districts[row[1]][row[2]].append({'name':row[0], 'number':row[3]})
  return jsonify(districts=districts)

def appplication_status(app):
    status = True
    if calculate_age(app.date_of_birth) < 12 or calculate_age(app.date_of_birth) > 55:
        status = False
    if app.read_english == 0:
        status = False
    if calculate_age(app.date_moved) < 2:
        status = False
    if app.brac_chp == 1:
        status = False
    if app.maths == 0 or app.english == 0 or app.about_you == 0:
        status = False
    if (app.maths + app.english + app.about_you) < 30:
        status = False
    return status
def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
def interview_pass(interview):
  status = False
  if interview.commitment >1 and interview.total_score > 24 and interview.special_condition == 'No':
    status = True
  return status
