import time
import uuid

from flask import json

from app import db
from app.models import Registration, Education


class CreateRegistationsFromCsv():
    COLUMNS = [
        'name',
        'phone',
        'gender',
        'education'
    ]
    
    def __init__(self, recruitment=None):
        if recruitment is None:
            raise Exception('Invalid Recruitment')
        
        self.recruitment = recruitment
    
    def generate_uuid(self):
        return str(uuid.uuid4())
    
    def get_education_id(self, education_level):
        education = Education.query.filter_by(name=education_level).first()
        if education:
            return education.id
        else:
            return 1  # Default
    
    def get_params(self, record):
        other = record.copy()
        args = {}
        for k in self.COLUMNS:
            if k == 'education':
                args[k] = self.get_education_id(other.get(k, None))
            else:
                args[k] = other.pop(k, None)
        
        args['other'] = json.dumps(other)
        return args
    
    def validate(self):
        for record in self.csv_rows:
            keys = list(record.keys())
            if set(keys) & set(self.COLUMNS) == set(self.COLUMNS):
                # All keys in available. Proceed to save
                print("Creating registrations")
                self.create_registation(self.get_params(record))
            else:
                raise Exception('Invalid registration details')
    
    def create_registation(self, args):
        
        args['recruitment'] = self.recruitment.id
        args['id'] = self.generate_uuid()
        args['country'] = self.recruitment.country
        args['added_by'] = 1
        args['client_time'] = time.time()
        
        registration = Registration(**args)
        db.session.add(registration)
    
    def run(self, csv_rows=None):
        if not isinstance(csv_rows, list) or csv_rows is None:
            raise Exception("Invalid parameters")
        self.csv_rows = csv_rows
        self.validate()
        db.session.commit()
