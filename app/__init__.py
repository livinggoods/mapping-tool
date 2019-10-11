import rq
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from redis import Redis

from config import config
from flask_googlemaps import GoogleMaps, Map



# initialize flask extensions
# note, extensions are initalized with no Flask app instance because
# application factor is being used
bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
admin = Admin()

login_manager = LoginManager()
login_manager.session_protection = 'strong'  # use strong session protection
login_manager.login_view = 'auth.login'  # set the endpoint for login page


def create_app(config_name):
    """
    Flask Application Factory that takes configuration settings and returns
    a Flask application.
    """
    # initalize instance of Flask application
    app = Flask(__name__)

    # import configuration settings into Flask application instance
    app.config['WHOOSH_BASE'] = '/tmp/whoosh'
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # initialize Flask extensions
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    admin = Admin(app, name='Admin', template_mode='bootstrap3')
    GoogleMaps(app)
    login_manager.init_app(app)
    
    # Tasks Management
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('expansion-tasks', connection=app.redis, default_timeout=5000)
    
    ## Add admin
    from .admins import TrainingStatusAdmin
    
    admin.add_view(TrainingStatusAdmin(db.session))
    

    # redirect all http requests to https
    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask.ext.sslify import SSLify
        sslify = SSLify(app)

    # register 'main' blueprint with Flask application
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # register 'administration' blueprint with Flask Application
    from .administration import administration as admin_blueprint
    # the 'url_prefix' parameter means all routes defined in the blueprint will
    # be registered with the prefix '/administration' (e.g., '/administration/users')
    app.register_blueprint(admin_blueprint, url_prefix='/administration')

    # register 'auth' blueprint with Flask application
    from .auth import auth as auth_blueprint
    # the 'url_prefix' parameter means all routes defined in the blueprint will
    # be registered with the prefix '/auth' (e.g., '/auth/login')
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # register 'search' blueprint with Flask application
    from .search import search as search_blueprint
    # the 'url_prefix' parameter means all routes defined in the blueprint will
    # be registered with the prefix '/search' (e.g., '/search/_prefetch')
    app.register_blueprint(search_blueprint, url_prefix='/search')

    # register 'api' blueprint with Flask application
    from .api import api as api_blueprint
    # the 'url_prefix' parameter means all routes defined in the blueprint will
    # be registered with the prefix '/api/v1' (e.g., '/api/v1/relationships')
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')
    # register 'version 2' blueprint with Flask application
    app.register_blueprint(api_blueprint, url_prefix='/api/v2')


    return app
