from . import api_v2 as api
from flask import jsonify


@api.app_errorhandler(400)
def bad_request(e):
    return jsonify(error='Bad requests'), 400


@api.app_errorhandler(401)
def unauthorized(e):
    return jsonify(error='Unauthorized'), 401


@api.app_errorhandler(404)
def unauthorized(e):
    return jsonify(error='Not found'), 404


@api.app_errorhandler(500)
def unauthorized(e):
    return jsonify(error='Server error'), 500
