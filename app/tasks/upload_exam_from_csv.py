import uuid

from app import db
from app.models import ExamTraining, Question


class UploadExamFromCSV():
    """
    Task to upload examination from CSV rows
    """
    
    EXAM_FIELDS = {
        'title',
        'country'
    }
    
    QUESTION_FIELDS = {
        'question',
        'allocated_marks',
        'batch_id',
        'country'
    }
    
    CHOICES_FIELDS = {
        'question_id',
        'question_choice',
        'is_answer',
        'allocated_marks',
        'country'
    }

    EXAM_QUESTION_FIELDS = {
        'exam_id',
        'question_id',
        'weight',
        'allocated_marks',
        'country'
    }
    
    def __init__(self):
        """
        Constructor
        """
        self.batch_id = self.create_uuid()
    
    def create_uuid(self):
        """
        Create a UUID 4 string
        :return: Valid UUID 4 String
        """
        return str(uuid.uuid4())
    
    def create_question(self, args):
        """
        Create Question from args
        :param args:
        :return:
        """
        pass
        
    
    def create_question_choice(self, exam, args):
        """
        Create question choice from args
        :param args:
        :return:
        """
        assert isinstance(exam, ExamTraining), "Invalid arguments"
        
    
    def create_exam(self, args):
        """
        Create exams from args
        :param args:
        :return:
        """
        assert isinstance(args, dict)
        
        keys = {k for k, v in args.iteritems()}
        if keys & self.EXAM_FIELDS == self.EXAM_FIELDS:
            # Valid
            exam = ExamTraining(**args)
            db.session.add(exam) # TODO Need to commit to db to generate exam.id
            return exam
        else:
            raise Exception('Invalid arguments. Could not create exam')
        
    
    def validate(self, csv_rows):
        """
        Validates if input is valid.
        :return:
        """
        for record in csv_rows:
            
            
            record['batch_id'] = self.batch_id
            record['country'] = self.country
            keys = {k for k, v in record.iteritems()}
            if keys & self.QUESTION_FIELDS == self.QUESTION_FIELDS:
                self.create_question(csv_rows)
            else:
                raise Exception("CSV does not contain ")
        
        
    
    def run(self, csv_rows, country, *args, **kwargs):
        assert isinstance(csv_rows, list), 'Invalid arguments. CSV rows must be a list'
        assert country is not None, 'Invalid country argument'
        
        self.country = country
        
        title = kwargs.get('title', None)
        exam_status_id = kwargs.get('exam_status_id', None)
        passmark = kwargs.get('passmark', None)
        is_certification = kwargs.get('is_certification', None)
        certification_type = kwargs.get('certification_type', None)
        
        assert title is not None, "Invalid exam title"
        assert country is not None, "Invalid exam country"
        assert isinstance(is_certification, bool), 'Invalid is certification'
        
        self.validate(csv_rows)