from flask import render_template, redirect, url_for, flash, request, abort, \
    current_app, jsonify, make_response, json
from flask_login import current_user, login_required
from ..models import User, Location, IccmComponents
from ..main.forms import IccmComponentForm
from ..decorators import admin_required, permission_required
from werkzeug.utils import secure_filename
from .. import db, admin
from . import administration
from .forms import UploadLocationForm
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

                constituency = Location.query.filter_by(name=phone.get('Constituency'), admin_name='Constituency')
                if not constituency:
                    constituency = Location(name=phone.get('Constituency'), parent=district.id, admin_name='Constituency',
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