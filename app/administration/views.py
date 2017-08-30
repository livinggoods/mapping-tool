from flask import render_template, redirect, url_for, flash, request, abort, \
    current_app, jsonify, make_response
from flask_login import current_user, login_required
from ..models import User, Geo, IccmComponents
from ..main.forms import IccmComponentForm
from ..decorators import admin_required, permission_required
from .. import db, admin
from . import administration
import time


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