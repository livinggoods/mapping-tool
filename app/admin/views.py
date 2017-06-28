from flask import render_template, redirect, url_for, flash, request, abort, \
    current_app, jsonify, make_response
from flask_login import current_user, login_required
from ..models import User, Geo
from .. import db
from . import admin


@admin.route('/users', methods=['GET'])
@login_required
def admin_index():
    page={'title':'Users','subtitle':'Registered Users'}
    users = User.query.order_by(User.username.asc()).all()
    usr = []
    for user in users:
        usr.append({'name':user.name, 'email':user.email})
    # return jsonify(users=usr)
    return render_template('users.html', page=page, users=users)


@admin.route('/user', methods=['POST'])
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