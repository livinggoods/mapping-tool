from flask import jsonify, request
from flask_login import current_user

from app.models import ErrorLog
from . import api as api
from .. import db


def log_api_error(request, e, code):
    
    payload = request.get_data()
    method = request.method
    headers = request.headers
    endpoint = request.full_path
    user = current_user.id if current_user.is_authenticated() else None
    
    log = ErrorLog(
        error=str(e),
        endpoint=str(endpoint),
        payload=str(payload),
        user=user,
        http_method=method,
        http_headers=str(headers),
        http_response_status_code=code
    )
    db.session.rollback()
    db.session.add(log)
    db.session.commit()
    db.session.close()
    

@api.app_errorhandler(400)
def bad_request(e):
    log_api_error(request=request, e=e, code=400)
    return jsonify(error='Bad requests'), 400


@api.app_errorhandler(401)
def unauthorized(e):
    log_api_error(request=request, e=e, code=401)
    return jsonify(error='Unauthorized'), 401


@api.app_errorhandler(404)
def not_found(e):
    return jsonify(error='Not found'), 404


@api.app_errorhandler(405)
def not_allowed(e):
    return jsonify(error='Not allowed'), 405


@api.app_errorhandler(500)
def server_error(e):
    log_api_error(request=request, e=e, code=500)
    return jsonify(error='Server error'), 500


@api.errorhandler(Exception)
def error_handler(e):
    log_api_error(request=request, e=e, code=500)
    return jsonify(error="Server error"), 500
