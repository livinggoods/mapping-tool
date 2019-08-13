#!/usr/bin/env python
import os
import uuid

import rq
from flask import current_app
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Shell

from app import create_app, db
from app.models import User, Role, Geo, UserType, Location, Education, ErrorLog, ExamResult, Task
from app.utils.generate_registrations_command import GenerateRegistrations

application = create_app(os.getenv('FLASK_CONFIG', 'default'))
manager = Manager(application)
migrate = Migrate(application, db)


def make_shell_context():
    """
    Automatically import application, db, and model objects into interactive
    shell.
    """
    return dict(application=application, db=db, User=User, Geo=Geo, Role=Role, UserType=UserType)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)
manager.add_command("fake_registrations", GenerateRegistrations())


@manager.command
def test():
    """
    Run the unit tests.
    """
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def db_update_education():
    # insert education data
    Education.create_education()


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
        app_name='password'.encode('base64'),
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
        app_name='webmaster'.encode('base64'),
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
    print '-' * 17
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
    
    # insert education data
    Education.create_education()


@manager.command
def resolve_errors():
    import requests
    endpoint = '/api/v1/sync/mapping?'
    errors = iter(ErrorLog.query.filter_by(resolved=False, endpoint=endpoint).order_by(ErrorLog.id.desc()))
    
    while True:
        try:
            
            error = errors.next()
            
            base_url = 'https://expansion.lg-apps.com'
            url = base_url + error.endpoint
            headers = {}
            for item in error.http_headers.split("\n"):
                item = str(item).strip()
                header = item.split(': ')
                if len(header) == 2:
                    headers[header[0]] = header[1]
            
            method_type = error.http_method
            payload = error.payload
            
            if method_type == 'POST':
                r = requests.post(url=url, data=payload.encode('utf-8'), headers=headers)
                if 200 <= r.status_code < 300:
                    db.session.delete(error)
                    db.session.commit()
                    print "Resolved " + error.error
                else:
                    print "Failed to resolve " + error.error
        
        except StopIteration as e:
            break
        except Exception as e:
            print str(e)
            break


@manager.command
def migrate_to_uuid():
    # select * records in the table
    records = ExamResult.query.all()
    total = str(len(records))
    i = 1
    for record in records:
        print "Migrating {} of {}".format(str(i), total)
        record.id = str(uuid.uuid4())
        db.session.commit()
        i = i + 1
    print "Migration complete. {} records migrated".format(total)


@manager.command
def requeue_tasks():
    tasks = Task.query.filter_by(complete=False)
    for task in tasks:
        rq.requeue_job(task.id, connection=current_app.redis)


@manager.command
def update_recruitment_name():
    from app.models import Recruitments, Training
    recruitments = Recruitments.query.filter(Recruitments.cohort_id.isnot(None))
    for recruitment in recruitments:
        old_name = recruitment.name
        cohort = recruitment.cohort
        branch = cohort.branch
        recruitment.name = '%s Cohort %s' % (branch.branch_name, cohort.cohort_number)
        db.session.merge(recruitment)
        print 'RENAMING RECRUITMENT', '%s --> %s' % (old_name, recruitment.name)
        
        # Rename training
        training = Training.query.filter_by(recruitment_id=recruitment.id).first()
        if training:
            old_name = training.training_name
            training.training_name = '%s Cohort %s' % (branch.branch_name, cohort.cohort_number)
            db.session.merge(training)
            print 'RENAMING Training', '%s --> %s' % (old_name, training.training_name)
        
    db.session.commit()


if __name__ == '__main__':
    manager.run()
