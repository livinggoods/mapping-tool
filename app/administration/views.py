import os
import time
import traceback
import uuid

from flask import render_template, redirect, url_for, request, current_app, jsonify, make_response, json, abort, flash, session
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.tasks.create_registations_from_csv import CreateRegistationsFromCsv
from . import administration
from .forms import UploadLocationForm, LocationUgForm
from .. import db
from ..decorators import admin_required
from ..main.forms import IccmComponentForm
from ..models import User, Location, IccmComponents, ErrorLog, Role, Mapping, Training, Recruitments, Registration, \
    Branch, Cohort
from ..utils.utils import process_csv


@administration.route('/', methods=['GET'])
@login_required
def admin_dashboard():
    return make_response(jsonify(status='dashboard coming soon'), 200)


@administration.route('/users', methods=['GET'])
@login_required
def admin_users():
    page = {'title': 'Users', 'subtitle': 'Registered Users'}
    users = User.query.order_by(User.username.asc()).all()
    roles = Role.query.all()
    usr = []
    for user in users:
        usr.append({'name': user.name, 'email': user.email, 'role': user.role_id})
    # return jsonify(users=usr)
    return render_template('admin/users.html', page=page, users=users, roles=roles)


@administration.route('/user', methods=['POST'])
@login_required
def user_action():
    if request.method == 'POST':
        user = request.form.get('user'),
        if user != '':
            status = ''
            user = User.query.filter_by(id=user).first()
            if (user.confirmed):
                user.confirmed = False
                status = 'unconfirmed'
            else:
                user.confirmed = True
                status = 'confirmed'
            db.session.commit()
            return jsonify(user=user.id, name=user.name, status=status)
        else:
            return make_response(jsonify(status='user must be specified'), 404)
    else:
        return make_response(jsonify(status='not allowed'), 405)


@administration.route('/iccm-components/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_iccm_components(id):
    form = IccmComponentForm()
    iccm = IccmComponents.query.filter_by(id=id).first()
    if form.validate_on_submit():
        message = ''
        if iccm:
            iccm.component_name = form.component_name.data
            iccm.added_by = current_user.id
            iccm.comment = form.comment.data
            iccm.client_time = int(time.time())
            db.session.add(iccm)
            message = 'Record updated'
        else:
            component = IccmComponents(
                component_name=form.component_name.data,
                added_by=current_user.id,
                comment=form.comment.data,
                client_time=int(time.time())
            )
            db.session.add(component)
            message = 'Record created'
        db.session.commit()
        return redirect(url_for('admin.iccm_components'))
    # set inital values
    form.component_name.data = iccm.component_name
    form.comment.data = iccm.comment
    return render_template('new_iccm.html', form=form)


@administration.route('/iccm-components/new', methods=['GET', 'POST'])
@login_required
def new_iccm_components():
    form = IccmComponentForm()
    if request.method == 'GET':
        return render_template('new_iccm.html', form=form)
    else:
        if form.validate_on_submit():
            component = IccmComponents(
                component_name=form.component_name.data,
                added_by=current_user.id,
                comment=form.comment.data,
                client_time=int(time.time())
            )
            db.session.add(component)
            db.session.commit()
        return redirect(url_for('admin.iccm_components'))


@administration.route('/iccm-components', methods=['GET'])
@login_required
def iccm_components():
    iccms = IccmComponents.query.filter_by(archived=0)
    return render_template('iccm.html', iccms=iccms)


@administration.route('/location-update', methods=['GET'])
@login_required
def location_test():
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'data', 'ug_locations.csv')
    data = process_csv(path)
    for phone in data:
        # check if the Region Exists
        region = Location.query.filter_by(name=phone.get('Region').title(), admin_name='Region').first()
        if not region:
            region = Location(name=phone.get('Region').title(), parent=2, admin_name='Region', country='UG')
        region.name = phone.get('Region').title()
        db.session.add(region)
        db.session.commit()
        
        district = Location.query.filter_by(name=phone.get('District').title(), admin_name='District').first()
        if not district:
            district = Location(name=phone.get('District').title(), parent=region.id, admin_name='District',
                                country='UG')
        district.name = phone.get('District').title()
        db.session.add(district)
        db.session.commit()
        
        constituency = Location.query.filter_by(name=phone.get('County').title(), admin_name='County').first()
        if not constituency:
            constituency = Location(name=phone.get('County').title(), parent=district.id, admin_name='County',
                                    country='UG')
        constituency.name = phone.get('County').title()
        db.session.add(constituency)
        db.session.commit()
        
        sub_county = Location.query.filter_by(name=phone.get('Sub-County').title(), admin_name='Sub-County').first()
        if not sub_county:
            sub_county = Location(name=phone.get('Sub-County').title(), parent=constituency.id, admin_name='Sub-County',
                                  country='UG')
        sub_county.name = phone.get('Sub-County').title()
        db.session.add(sub_county)
        db.session.commit()
        
        parish = Location.query.filter_by(name=phone.get('Parish').title(), admin_name='Parish').first()
        if not parish:
            parish = Location(name=phone.get('Parish').title(), parent=sub_county.id, admin_name='Parish',
                              country='UG')
        parish.name = phone.get('Parish').title()
        db.session.add(parish)
        db.session.commit()
        
        village = Location.query.filter_by(name=phone.get('Village').title(), admin_name='Village').first()
        if not village:
            village = Location(name=phone.get('Village').title(), parent=parish.id, admin_name='Village',
                               country='UG')
        village.name = phone.get('Village').title()
        db.session.add(village)
        db.session.commit()
    return jsonify(data=data)


@administration.route('/locations', methods=['GET', 'POST'])
@login_required
def location_administration():
    form = UploadLocationForm()
    if request.method == 'GET':
        locations = Location.query.all()
        return render_template('admin/locations.html', locations=locations, form=form)
    else:
        if form.validate_on_submit():
            f = form.file_field.data
            filename = secure_filename(f.filename)
            
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'data', filename)
            f.save(path)
            data = process_csv(path)
            for phone in data:
                # check if the Region Exists
                region = Location.query.filter_by(name=phone.get('Region'), admin_name='Region')
                if not region:
                    region = Location(name=phone.get('Region'), parent=2, admin_name='Region', country='UG')
                    db.session.add(region)
                    db.session.commit()
                
                district = Location.query.filter_by(name=phone.get('District'), admin_name='District')
                if not district:
                    district = Location(name=phone.get('District'), parent=region.id, admin_name='District',
                                        country='UG')
                    db.session.add(district)
                    db.session.commit()
                
                constituency = Location.query.filter_by(name=phone.get('County'), admin_name='County')
                if not constituency:
                    constituency = Location(name=phone.get('County'), parent=district.id, admin_name='County',
                                            country='UG')
                    db.session.add(constituency)
                    db.session.commit()
                
                sub_county = Location.query.filter_by(name=phone.get('Sub-County'), admin_name='Sub-County')
                if not sub_county:
                    sub_county = Location(name=phone.get('Sub-County'), parent=constituency.id, admin_name='Sub-County',
                                          country='UG')
                    db.session.add(sub_county)
                    db.session.commit()
                
                parish = Location.query.filter_by(name=phone.get('Parish'), admin_name='Parish')
                if not parish:
                    parish = Location(name=phone.get('Parish'), parent=sub_county.id, admin_name='Parish',
                                      country='UG')
                    db.session.add(parish)
                    db.session.commit()
                
                village = Location.query.filter_by(name=phone.get('Village'), admin_name='Village')
                if not village:
                    village = Location(name=phone.get('Village'), parent=parish.id, admin_name='Village',
                                       country='UG')
                    db.session.add(village)
                    db.session.commit()
            return jsonify(status='created')
        else:
            return jsonify(filename='none')


@administration.route('/location_data', methods=['GET', 'POST'])
@login_required
def administration_location_data():
    if request.method == 'GET':
        page_data = {'title': 'Location Data',
                     'subtitle': 'List of location data'}
        locations = Location.query.filter_by(archived=0)
        page = request.args.get('page', 1, type=int)
        pagination = locations.paginate(page, per_page=current_app.config['PER_PAGE'], error_out=False)
        return render_template('admin/location_data.html',
                               endpoint='administration.administration_location_data',
                               pagination=pagination, page=page_data, locations=locations)
    else:
        return jsonify(filename='none')


@administration.route('/location/new', methods=['GET', 'POST'])
@administration.route('/location/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def location_administration_edit(id=None):
    form = LocationUgForm()
    form.parent.choices = [(a.id, a.name) for a in \
                           Location.query.filter(Location.admin_name.in_(['District', 'County'])).order_by('name')]
    if form.validate_on_submit():
        if id is not None:
            location = Location.query.filter_by(id=id).first()
            location.name = form.name.data
            location.parent = form.parent.data
            db.session.add(location)
            db.session.commit()
        else:
            location = Location(name=form.name.data,
                                parent=form.parent.data)
            db.session.add(location)
            db.session.commit()
        return redirect(url_for('administration.administration_location_data'))
    if id is not None:
        pass
        loc = Location.query.filter_by(id=id).first()
        form.name.data = loc.name
        form.parent.data = loc.parent
    return render_template('new_location.html', form=form)


@administration.route('/locations-displays', methods=['POST'])
def locations_display():
    if request.data is None:
        return jsonify({"status": "error"})
    location_obj = Location.query.filter_by(name=str(request.form.get('name'))).first_or_404()
    response_obj = []
    response = {}
    locations = Location.query.filter_by(parent=location_obj.id).all()
    for location in locations:
        response_obj.append({
            'name': location.name, 'id': location.id
        })
    response['locations'] = response_obj
    return jsonify(response)


@administration.route("/errors")
@login_required
def view_api_error_logs():
    page_data = {
        'title': 'Unsolved API Errors',
        'subtitle': 'View API error logs'
    }
    
    errors = ErrorLog.query.filter_by(resolved=False)
    pagination_count = request.args.get('page', 1, type=int)
    pagination = errors.paginate(pagination_count, per_page=current_app.config['PER_PAGE'], error_out=False)
    
    return render_template("admin/api_error_logs.html",
                           errors=errors,
                           page=page_data,
                           endpoint='administration.view_api_error_logs',
                           pagination=pagination,
                           )


@administration.route("/error/<int:error_id>", methods=['GET', 'POST'])
@login_required
def view_api_error_log(error_id):
    page_data = {
        'title': 'Error Details',
        'subtitle': 'Error Details'
    }
    
    error = ErrorLog.query.filter_by(id=error_id).first_or_404()
    
    if request.method == 'GET':
        
        return render_template('admin/api_error_log.html',
                               page=page_data,
                               error=error)
    else:
        db.session.delete(error)
        db.session.commit()
        return redirect(url_for('administration.view_api_error_logs'))


@administration.route("/other", methods=['GET', 'POST'])
@login_required
def view_other():
    page_data = {
        'title': 'Control',
        'subtitle': 'Error Details'
    }
    
    if request.method == 'GET':
        
        return render_template('admin/other.html',
                               page=page_data)
    else:
        return jsonify({
            'status': 'Development !!!'
        })


@administration.route('/adminapi', methods=['POST'])
def admin_action():
    if request.method == 'POST':
        if request.data is None:
            return jsonify({'status': 'empty'})
        else:
            if request.form.get('action') == 'user_records':
                usr_objs = User.query.filter_by(archived=0).all()
                response = {}
                response_obj = []
                for user in usr_objs:
                    response_obj.append({'username': user.username, 'id': user.id})
                response['status'] = 'ok'
                response['users'] = response_obj
                return jsonify(response)
            elif request.form.get('action') == 'mapping_records':
                mapping_objs = Mapping.query.filter_by(archived=0).all()
                response = {}
                response_obj = []
                for mapping in mapping_objs:
                    response_obj.append({'name': mapping.name, 'id': mapping.id})
                response['status'] = 'ok'
                response['mappings'] = response_obj
                return jsonify(response)
            elif request.form.get('action') == 'recruitment_records':
                recruitment_objs = Recruitments.query.filter_by(archived=0).all()
                response = {}
                response_obj = []
                for recruitment in recruitment_objs:
                    response_obj.append({'name': recruitment.name, 'id': recruitment.id})
                response['status'] = 'ok'
                response['recruitments'] = response_obj
                return jsonify(response)
            elif request.form.get('action') == 'training_records':
                training_objs = Training.query.filter_by(archived=0).all()
                response = {}
                response_obj = []
                for training in training_objs:
                    response_obj.append({'name': training.training_name, 'id': training.id})
                response['status'] = 'ok'
                response['trainings'] = response_obj
                return jsonify(response)
            elif request.form.get('action') == 'archieve':  # achieve records
                if request.form.get('entity') == 'user':
                    usr_obj = User.query.filter_by(id=request.form.get('id')).first_or_404()
                    usr_obj.archived = 1
                    return jsonify({'status': 'ok', 'message': 'record updated !!!'})
                elif request.form.get('entity') == 'mapping':
                    mapping_obj = Mapping.query.filter_by(id=request.form.get('id')).first_or_404()
                    mapping_obj.archived = 1
                    return jsonify({'status': 'ok', 'message': 'record archieved !!!'})
                elif request.form.get('entity') == 'recruitment':
                    recruitment_obj = Recruitments.query.filter_by(id=request.form.get('id')).first_or_404()
                    recruitment_obj.archived = 1
                    return jsonify({'status': 'ok', 'message': 'record updated !!!'})
                elif request.form.get('entity') == 'training':
                    training_obj = Training.query.filter_by(id=request.form.get('id')).first_or_404()
                    training_obj.archived = 1
                    return jsonify({'status': 'ok', 'message': 'record updated !!!'})
            elif request.form.get('action') == 'archieved':
                if request.form.get('entity') == 'users':
                    usr_obj = User.query.filter_by(archived=1).all()
                    response = {}
                    response_obj = []
                    for recruitment in usr_obj:
                        response_obj.append({'name': recruitment.username, 'id': recruitment.id})
                    response['status'] = 'ok'
                    response['users'] = response_obj
                    return jsonify(response)
                elif request.form.get('entity') == 'mappings':
                    mapping_obj = Mapping.query.filter_by(archived=1).all()
                    response = {}
                    response_obj = []
                    for mapping in mapping_obj:
                        response_obj.append({'name': mapping.name, 'id': mapping.id})
                    response['status'] = 'ok'
                    response['mappings'] = response_obj
                    return jsonify(response)
                elif request.form.get('entity') == 'recruitments':
                    recruitment_obj = Recruitments.query.filter_by(archived=1).all()
                    response = {}
                    response_obj = []
                    for recruitment in recruitment_obj:
                        response_obj.append({'name': recruitment.name, 'id': recruitment.id})
                    response['status'] = 'ok'
                    response['recruitments'] = response_obj
                    return jsonify(response)
                elif request.form.get('entity') == 'trainings':
                    training_obj = Training.query.filter_by(archived=1).all()
                    response = {}
                    response_obj = []
                    for training in training_obj:
                        response_obj.append({'name': training.training_name, 'id': training.id})
                    response['status'] = 'ok'
                    response['trainings'] = response_obj
                    return jsonify(response)
                else:
                    return jsonify({'status': 'Error Archieved !!!'})
            elif request.form.get('action') == 'unachieve':  # unachieve records
                if request.form.get('entity') == 'user':
                    usr_obj = User.query.filter_by(id=request.form.get('id')).first_or_404()
                    usr_obj.archived = 0
                    return jsonify({'status': 'ok', 'message': 'record unachieved !!!'})
                elif request.form.get('entity') == 'mapping':
                    mapping_obj = Mapping.query.filter_by(id=request.form.get('id')).first_or_404()
                    mapping_obj.archived = 0
                    return jsonify({'status': 'ok', 'message': 'record unachieved !!!'})
                elif request.form.get('entity') == 'recruitment':
                    recruitment_obj = Recruitments.query.filter_by(id=request.form.get('id')).first_or_404()
                    recruitment_obj.archived = 0
                    return jsonify({'status': 'ok', 'message': 'record unachieved !!!'})
                elif request.form.get('entity') == 'training':
                    training_obj = Training.query.filter_by(id=request.form.get('id')).first_or_404()
                    training_obj.archived = 0
                    return jsonify({'status': 'ok', 'message': 'record unachieved !!!'})
            elif request.form.get('action') == 'change_user_role':
                role_obj = Role.query.filter_by(name=request.form.get('role')).first_or_404()
                usr_obj = User.query.filter_by(username=request.form.get('user')).first_or_404()
                usr_obj.role_id = role_obj.id
                return jsonify({"status": "ok", "message": "user role changed !!!"})
            else:
                return jsonify({'status': 'no action specified'})
    else:
        return jsonify({'status': 'get action'})


@administration.route("/search/chw", methods=['GET', 'POST'])
@login_required
def search_chw():
    """
    GET:  Search for CHW using either name or phone number
    :param query_type either name or telephone number
    :param query Phone number or name to search
    :return:
    
    POST: Update CHW with mm UUID from form in frontend
    :param uuid ID of the record to update
    :param mm_uuid MM UUID
    """
    QUERY_TYPES = [
        (1, 'Name'),
        (2, 'Phone Number')
    ]
    
    if request.method == 'GET':
        query_type = request.args.get('query_type', '')
        query = request.args.get('query', '')
        search_results = []
        page = {'title': 'Search CHW', 'subtitle': 'Search for All CHW Existing within Tremap'}
        
        if query != '':
            if query_type == '1':
                search_results = Registration.query.filter(Registration.name.like('%' + query + '%'),
                                                           Registration.country == current_user.location).all()
            elif query_type == '2':
                search_results = Registration.query.filter(Registration.phone.like('%' + query + '%'),
                                                           Registration.country == current_user.location).all()
        
        return render_template('admin/search_chw.html',
                               page=page,
                               query_type=query_type,
                               query=query,
                               query_types=QUERY_TYPES,
                               search_results=search_results)
    else:
        query_type = request.args.get('query_type', '')
        query = request.args.get('query', '')
        uuid = request.form.get('uuid', None)
        mm_uuid = request.form.get('mm_uuid', None)
        if mm_uuid and uuid:
            registration = Registration.query.get_or_404(uuid)
            other = json.loads(registration.other)
            other['mm_uuid'] = mm_uuid
            registration.other = json.dumps(other)
            db.session.merge(registration)
            db.session.commit()
            return redirect(
                url_for('administration.search_chw', query_type=query_type, query=query, operation='success'))
        else:
            return redirect(url_for('administration.search_chw', query_type=query_type, query=query, operation='fail'))


@administration.route('/branch/add', methods=['GET', 'POST'])
@login_required
def add_new_branch():
    if request.method == 'GET':
        page = {'title': 'Add new branch', 'subtitle': 'Add new branch'}
        districts = Location.query.filter_by(admin_name='District')
        return render_template('admin/add_branch.html',
                               page=page,
                               districts=districts)
    else:
        branch_name = request.form.get('branch_name', None)
        county_id = request.form.get('county_id', None)
        subcounty_id = request.form.get('subcounty_id', None)
        district_id = request.form.get('district_id', None)
        
        branch = Branch(id=str(uuid.uuid4()),
                        branch_name=branch_name,
                        county_id=county_id,
                        subcounty_id=subcounty_id,
                        country=current_user.location,
                        district_id=district_id )
        db.session.add(branch)
        db.session.commit()
        return redirect(url_for('administration.view_all_branches'))
    
    
@administration.route('/branches', methods=['GET'])
@login_required
def view_all_branches():
    """
    GET: Shows a list of all the branches
    :return:
    """
    page = {'title': 'List of all Branches', 'subtitle': 'List of all Branches'}
    branches = Branch.query.filter_by(country=current_user.location)
    pagination_count = request.args.get('page', 1, type=int)
    pagination = branches.paginate(pagination_count, per_page=current_app.config['PER_PAGE'], error_out=False)
    return render_template('admin/branch_list.html',
                           page=page,
                           endpoint='administration.view_all_branches',
                           pagination=pagination
                           )


@administration.route("/recruitment", methods=['GET', 'POST'])
@login_required
def recruitment():
    if request.method == 'GET':
        page = {'title': 'Recruitments', 'subtitle': 'Recruitments'}
        branches = Branch.query.filter_by(country=current_user.location)
        recruitments = Recruitments.query.filter_by(archived=0, country=current_user.location, cohort_id=None)
        return render_template('admin/recruitment.html',
                               page=page,
                               branches=branches,
                               recruitments=recruitments)
    else:
        recruitment_type = request.form.get('recruitment_type', None)
        if recruitment_type == 'select_recruitment':
            branch_id = request.form.get('branch_id', None)
            branch = Branch.query.get(branch_id)
            cohort_number = request.form.get('cohort_number', None)
            recruitment_id = request.form.get('recruitment_id', None)
            
            cohort = Cohort.query.filter_by(branch_id=branch_id, cohort_number=cohort_number).first()
            if cohort is None:
                cohort = Cohort(cohort_name=branch.branch_name, cohort_number=cohort_number, branch_id=branch_id)
                db.session.add(cohort)
                db.session.commit()

            recruitment = Recruitments.query.get(recruitment_id)
            
            c_recruitments = Recruitments.query.filter_by(cohort_id=cohort.id).all()
            for r in c_recruitments:
                if r.id != recruitment.id:
                    r.cohort_id = None
                    db.session.merge(r)
                    
            recruitment.cohort_id = cohort.id
            recruitment.name = '%s Cohort %s' % (branch.branch_name, cohort.cohort_number)
            db.session.merge(recruitment)
            
            db.session.commit()
            session.pop('_flashes', None)
            flash("Successful", 'success')
            return redirect(url_for('administration.recruitment', operation='success'))
        elif recruitment_type == 'upload_recruitment':
            # Upload and save the CSV file somewhere
            # Validate the CSV file
            # Create recruitment
            # Create Registrations
            # Create cohort
            # Associate recruitment with cohort
            if 'recruitment_upload' not in request.files:
                return redirect(url_for('administration.recruitment', operation='fail', error='No file attached'))
            csv_file = request.files['recruitment_upload']
            abs_path = None
            
            if csv_file.filename == '' or not len(csv_file.filename.split('.')) > 1:
                return redirect(url_for('administration.recruitment', operation='fail', error='Invalid file'))
            else:
                try:
                    filename = secure_filename(csv_file.filename)
                    csv_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    abs_path = os.path.abspath(path)
                    csv_rows = process_csv(abs_path)
                    
                    def create_recruitment(branch, cohort):
                        name = '%s Cohort %s' % (branch.branch_name, cohort.cohort_number)
                        id = str(uuid.uuid4())
                        recruitment = Recruitments.query.filter_by(name=name).first()
                        if not recruitment:
                            recruitment = Recruitments(
                                id=id,
                                name=name,
                                added_by=current_user.id,
                                comment='',
                                client_time=time.time(),
                                country=branch.country,
                                cohort_id=cohort.id,
                                subcounty=branch.subcounty_id,
                                county=branch.county_id
                            )
                            db.session.add(recruitment)
                        return recruitment
                    
                    def create_cohort(args):
                        cohort = Cohort.query.filter_by(branch_id=args.get('branch_id', None), cohort_number=args.get('cohort_number', None)).first()
                        if cohort is None:
                            cohort = Cohort(**args)
                            db.session.add(cohort)
                            db.session.commit()
                        return cohort

                    branch_id = request.form.get('branch_id', None)
                    branch = Branch.query.get(branch_id)
                    cohort_number = request.form.get('cohort_number', None)
                    cohort = create_cohort({'branch_id': branch_id, 'cohort_number': cohort_number, 'cohort_name': branch.branch_name})
                    recruitment = create_recruitment(branch, cohort)
                    CreateRegistationsFromCsv(recruitment=recruitment).run(csv_rows=csv_rows)

                    try:
                        if abs_path:
                            os.remove(abs_path)
                    except Exception as e:
                        # TODO This is a silent error and needs to be logged
                        pass
                    session.pop('_flashes', None)
                    flash("Successfully uploaded", 'success')
                    return redirect(url_for('administration.recruitment', operation='success'))
                    
                except Exception as e:
                    print e
                    print traceback.format_exc()
                    session.pop('_flashes', None)
                    flash(str(e), 'error')
                    return redirect(url_for('administration.recruitment', operation='fail', error=str(e)))
        else:
            return abort(403)
