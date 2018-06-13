from . import api as api
from flask import jsonify


@api.app_errorhandler(400)
def bad_request(e):
    return jsonify(error='Bad requests'), 400


@api.app_errorhandler(401)
def unauthorized(e):
    return jsonify(error='Unauthorized'), 401


@api.app_errorhandler(404)
def not_found(e):
    return jsonify(error='Not found'), 404\
    

@api.app_errorhandler(405)
def not_allowed(e):
    return jsonify(error='Not allowed'), 405


@api.app_errorhandler(500)
def server_error(e):
    return jsonify(error='Server error'), 500
