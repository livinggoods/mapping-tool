from flask import render_template, redirect, url_for, flash, request, abort, \
    current_app, jsonify, make_response, json
from flask_login import current_user, login_required
from ..models import User, Location, IccmComponents, Geo
from ..main.forms import IccmComponentForm
from ..decorators import admin_required, permission_required
from werkzeug.utils import secure_filename
from .. import db, admin
from . import administration
from .forms import UploadLocationForm, LocationUgForm
from ..utils.utils import process_location_csv
import time
import os


@administration.route('/', methods=['GET'])
@login_required
def admin_dashboard():
    return make_response(jsonify(status='dashboard coming soon'), 200)

@administration.route('/users', methods=['GET'])
@login_required
def admin_users():
    page={'title':'Users','subtitle':'Registered Users'}
    users = User.query.order_by(User.username.asc()).all()
    usr = []
    for user in users:
        usr.append({'name':user.name, 'email':user.email})
    # return jsonify(users=usr)
    return render_template('admin/users.html', page=page, users=users)


@administration.route('/user', methods=['POST'])
@login_required
def user_action():
    if request.method=='POST':
        user = request.form.get('user'),
        if user != '':
            status=''
            user=User.query.filter_by(id=user).first()
            if (user.confirmed):
                user.confirmed=False
                status='unconfirmed'
            else:
                user.confirmed=True
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
            message='Record updated'
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
    data = process_location_csv(path)
    for phone in data:
        # check if the Region Exists
        region = Location.query.filter_by(name=phone.get('Region').title(), admin_name='Region').first()
        if not region:
            region = Location(name=phone.get('Region').title(), parent=2, admin_name='Region', country='UG')
        region.name=phone.get('Region').title()
        db.session.add(region)
        db.session.commit()

        district = Location.query.filter_by(name=phone.get('District').title(), admin_name='District').first()
        if not district:
            district = Location(name=phone.get('District').title(), parent=region.id, admin_name='District', country='UG')
        district.name=phone.get('District').title()
        db.session.add(district)
        db.session.commit()

        constituency = Location.query.filter_by(name=phone.get('County').title(), admin_name='County').first()
        if not constituency:
            constituency = Location(name=phone.get('County').title(), parent=district.id, admin_name='County',
                                    country='UG')
        constituency.name=phone.get('County').title()
        db.session.add(constituency)
        db.session.commit()

        sub_county = Location.query.filter_by(name=phone.get('Sub-County').title(), admin_name='Sub-County').first()
        if not sub_county:
            sub_county = Location(name=phone.get('Sub-County').title(), parent=constituency.id, admin_name='Sub-County',
                                  country='UG')
        sub_county.name=phone.get('Sub-County').title()
        db.session.add(sub_county)
        db.session.commit()

        parish = Location.query.filter_by(name=phone.get('Parish').title(), admin_name='Parish').first()
        if not parish:
            parish = Location(name=phone.get('Parish').title(), parent=sub_county.id, admin_name='Parish',
                              country='UG')
        parish.name=phone.get('Parish').title()
        db.session.add(parish)
        db.session.commit()

        village = Location.query.filter_by(name=phone.get('Village').title(), admin_name='Village').first()
        if not village:
            village = Location(name=phone.get('Village').title(), parent=parish.id, admin_name='Village',
                               country='UG')
        village.name=phone.get('Village').title()
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
            data = process_location_csv(path)
            for phone in data:
                # check if the Region Exists
                region = Location.query.filter_by(name=phone.get('Region'), admin_name='Region')
                if not region:
                    region = Location(name=phone.get('Region'), parent=2, admin_name='Region', country='UG')
                    db.session.add(region)
                    db.session.commit()

                district = Location.query.filter_by(name=phone.get('District'), admin_name='District')
                if not district:
                    district = Location(name=phone.get('District'), parent=region.id, admin_name='District', country='UG')
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
        page = {'title': 'Location Data',
                'subtitle': 'List of location data'}
        locations = Location.query.filter_by(archived=0)
        page = request.args.get('page', 1, type=int)
        pagination=locations.paginate(page, per_page=current_app.config['PER_PAGE'],error_out=False)
        return render_template('admin/location_data.html',
                               endpoint='administration.administration_location_data',
                               pagination=pagination, page=page)
    else:
        return jsonify(filename='none')


@administration.route('/location/new', methods=['GET', 'POST'])
@administration.route('/location/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def location_administration_edit(id=None):
    form = LocationUgForm()
    form.parent.choices = [(a.id, a.name) for a in \
                               Location.query.filter(Location.admin_name.in_(['District','County'])).order_by('name')]
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
