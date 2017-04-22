#!/usr/bin/env python
import os
from app import create_app, db
from app.models import User, Role, Geo, UserType, Location, Education
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from app.data import data

application = create_app(os.getenv('FLASK_CONFIG', 'default'))
manager = Manager(application)
migrate = Migrate(application, db)


def make_shell_context():
    """
    Automatically import application, db, and model objects into interactive
    shell.
    """
    return dict(application=application, db=db, User=User, Geo=Geo, Role=Role,
                Follow=Follow, FirmType=FirmType, FirmTier=FirmTier, Firm=Firm,
                Company=Company, Relationship=Relationship, UserType=UserType)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """
    Run the unit tests.
    """
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def db_rebuild():
    """
    Destroy and rebuild database with fake data.
    """
    # destroy and rebuild tables
    db.reflect()
    db.drop_all()
    db.create_all()

    # insert locations as defined in model
    Location.insert_locations()

    # insert roles as defined in model
    Role.insert_roles()

    # insert geos and usertypes as defined in model
    Geo.insert_geos()
    UserType.insert_user_types()

    # insert education data
    Education.create_education()


    # insert fake admin/test users
    from random import seed
    import forgery_py
    seed()
    test_user_1 = User(
        email='dkimaru@livinggoods.org',
        username='dkimaru',
        password='password',
        app_name ='password'.encode('base64'),
        confirmed=True,
        name='David Kimaru',
        location='KE',
        about_me=forgery_py.lorem_ipsum.sentence(),
        member_since=forgery_py.date.date(True)
    )
    admin_user = User(
        email='admin@livinggoods.org',
        username='webmaster',
        password='webmaster',
        app_name ='webmaster'.encode('base64'),
        confirmed=True,
        name='Web Master',
        location='UG',
        about_me=forgery_py.lorem_ipsum.sentence(),
        member_since=forgery_py.date.date(True)
    )
    db.session.add_all([test_user_1, admin_user])
    db.session.commit()

    # insert fake user data
    # User.generate_fake(60)


    # print results
    inspector = db.inspect(db.engine)
    print 'The following tables were created.'
    print '-'*17
    for table in inspector.get_table_names():
        print table


@manager.command
def deploy():
    """Run deployment tasks."""
    from flask.ext.migrate import upgrade

    # migrate database to latest revision
    upgrade()

    # create user roles
    Role.insert_roles()

    # insert geos and usertypes as defined in model
    Geo.insert_geos()
    UserType.insert_user_types()

    # insert firm types/tiers as defined in model


if __name__ == '__main__':
    manager.run()
