import random
import time
import uuid
import datetime

import forgery_py
from flask_script import Command

from app import db
from app.models import Recruitments, Registration, Education, EducationLevel


class GenerateRegistrations(Command):
    
    def run(self):
        try:
            recruitment = self.create_recruitment()
            
            registrations = self.create_registrations(recruitment=recruitment)
            for registration in registrations:
                db.session.add(registration[1])
                
                print '%s Creating Registration %s' % (registration[0], registration[1].name)
            
            db.session.commit()
        except Exception as e:
            print 'Exception %s'%str(e)
            db.session.rollback()
            
        finally:
            db.session.close()
    
    def create_recruitment(self):
        recruitment = Recruitments(
            id=str(uuid.uuid4()),
            name=forgery_py.name.location(),
            country='TZ',
            added_by=1,
            client_time=int(time.time()),
            date_added=forgery_py.date.date(True),
            synced=0,
            archived=0,
            county=1,
            status='draft'
        )
        db.session.add(recruitment)
        db.session.commit()
        
        print 'Created recruitment %s' % recruitment.name
        
        return recruitment
    
    def create_registrations(self, recruitment=None):
        if recruitment is None or not isinstance(recruitment, Recruitments):
            raise Exception('Invalid arguments exception')
        
        for i in range(0, 1200):
            
            education_level = self.create_education_level()
            
            registration = Registration(
                id=str(uuid.uuid4()),
                name=forgery_py.name.full_name(),
                phone=forgery_py.address.phone(),
                gender=forgery_py.personal.gender(),
                recruitment=recruitment.id,
                country='TZ',
                dob=time.mktime(forgery_py.date.date(past=True, min_delta=25, max_delta=60).timetuple()),
                comment=forgery_py.lorem_ipsum.sentence(),
                client_time=int(time.time()),
                assets_tracker_data=forgery_py.lorem_ipsum.sentence(),
                education=education_level.education_id
            )
            
            yield i, registration
            
    
    def create_education_level(self, ):
        education = self.create_education()
    
        education_level = EducationLevel(
            education_id=education.id,
            level_name=str(uuid.uuid4())
        )
        
        db.session.add(education_level)
        db.session.commit()
        
        return education_level
        
        
    
    def create_education(self):
        
        level_type = 'primary'
        
        education = Education.query.filter_by(level_type=level_type).first()
        
        if not education:
            education = Education(
                name=str(uuid.uuid4()),
                level_type=level_type,
                country='TZ'
            )
            db.session.add(education)
            db.session.commit()
        
        return education
