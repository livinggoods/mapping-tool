import time
import uuid
import re

from flask import json
from datetime import datetime

from app import db
from app.models import Registration, Education, Recruitments


class CreateRegistationsFromCsv():
    """
    Create a registration from CSV
    """
    
    # Mandatory CSV columns
    COLUMNS = [
        'name',
        'phone',
        'gender',
        'education',
        'dob', # YYYY-mm-dd format
        'feature',
        'proceed',
        'village'
    ]
    
    def __init__(self, recruitment=None):
        """
        Constructor
        :param recruitment: Recruitments object
        """
        assert isinstance(recruitment, Recruitments), 'Invalid recruitment'
        self.recruitment = recruitment
    
    def generate_uuid(self):
        """
        Generates a UUID4 string
        :return:
        """
        return str(uuid.uuid4())
    
    def get_education_id(self, education_level):
        """
        Return ID of education level from the database
        :param education_level: Education level
        :return: ID of education level
        """
        education = Education.query.filter_by(name=education_level).first()
        if education:
            return education.id
        else:
            return 1  # Default
    
    def clean_csv_rows(self, row):
        """
        Clean CSV rows. CSV may contain some empty rows or invalid encoding
        :param row:
        :return:
        """
        cleaned_args = {}
        for k, v in row.iteritems():
            if str(k).strip() == 'education': # Special case
                cleaned_args[k] = v
                continue
                
            if str(k).strip() == 'dob':
                cleaned_args[k] = self.process_dob(v)
                continue
                
            if str(k).strip() == 'proceed':
                cleaned_args[k] = self.process_proceed(v)
                continue
                
            if str(k).strip() == 'feature':
                cleaned_args[k] = v
                continue
                
            if k and v:
                k = re.sub(r'[\']', '', str(k)).strip()
                cleaned_args[k] = re.sub(r'[\']', '', str(v)).strip()
        return cleaned_args
        
    def process_proceed(self, csv_value):
        """
        Check proceed value in CSV
        :param csv_value:
        :return:
        """
        if str(csv_value).lower() == 'y' or str(csv_value).lower() == 'yes' or str(csv_value).lower() == '1':
            return 1
        else:
            return 0
        
    def process_dob(self, csv_value):
        """
        Return a timestamp from given date
        :param csv_value:
        :return:
        """
        dob = datetime.strptime(csv_value, '%Y-%m-%d')
        return int(time.mktime(dob.timetuple()) + dob.microsecond / 1000000.0) * 1000
    
    def get_params(self, record):
        """
        Creates a dictionary with necessary params for creating a new registration
        :param record: Dictionary containing CSV record
        :return: Cleaned dictionary containing keys needed to map to registration object
        """
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
        """
        Validates input from CSV rows. Checks if each row is valid
        :return: None
        """
        index = 0
        for record in self.csv_rows:
            record = self.clean_csv_rows(record)
            keys = list(record.keys())
            if set(keys) & set(self.COLUMNS) == set(self.COLUMNS):
                self.create_registation(self.get_params(record))
                index += 1
            else:
                raise Exception('Record at line %s missing: %s' % (index + 1, set(self.COLUMNS) - set(keys) & set(self.COLUMNS)))
    
    def create_registation(self, args):
        """
        Creates a registration object on the database
        :param args: Dictionary containing registration object values.
        :return: None
        """
        args['recruitment'] = self.recruitment.id
        args['id'] = self.generate_uuid()
        args['country'] = self.recruitment.country
        args['added_by'] = 1
        args['client_time'] = time.time()
        
        registration = Registration.query.filter_by(name=args['name'], phone=args['phone']).first()
        if registration:
            # Name, Phone, ID, Added by, client time cannot change
            CONSTANT_KEYS = [
                'name',
                'phone',
                'id',
                'added_by',
                'client_time'
            ]
            for k, v in args.iteritems():
                if k not in CONSTANT_KEYS:
                    setattr(registration, k, v)
            db.session.merge(registration)
        else:
            registration = Registration(**args)
            db.session.add(registration)
    
    def run(self, csv_rows=None):
        """
        Initiates task
        :param csv_rows: CSV rows containing registration details
        :return:
        """
        assert isinstance(csv_rows, list), 'Invalid parameters'
        self.csv_rows = csv_rows
        self.validate()
        db.session.commit()
