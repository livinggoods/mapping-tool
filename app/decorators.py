from functools import wraps
from flask import abort, request
from flask_login import current_user, login_user
from .models import Permission, User


def permission_required(permission):
    """
    Takes a permission function as an argument and returns a decorated
    function.
    """
    def decorator(f):
        @wraps(f)  # wraps keeps the name and docstring of the decorated func
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)


def api_login_required(f):
    """
    api_login_decorator which checks whether the requests are authenticated.
    
    We also need to ensure that if a user is logged in, they should be able to access the API.
    :param f:
    :return:
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.is_authenticated():
                return f(*args, **kwargs)
            token_details = request.headers.get('Authorization', '').split(' ')
            if len(token_details) > 1:
                token = token_details[1]
                user = User.verify_auth_token(token)
                if user:
                    if not user.is_authenticated():
                        login_user(user)
                    return f(*args, **kwargs)
            else:
                abort(401)
            return f(*args, **kwargs)
        return decorated_function
    return decorator(f)