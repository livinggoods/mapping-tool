import uuid

from app import db
from app.models import ExamTraining, Question, QuestionChoice, ExamQuestion


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
    
    def __init__(self, country):
        """
        Constructor
        """
        assert country is not None, "Invalid country argument"
        
        self.batch_id = self.create_uuid()
        self.country = country
    
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
        question = Question(**args)
        db.session.add(question)
        db.session.commit()
        return question
    
    def create_question_choice(self, args):
        """
        Create question choice from args
        :param args:
        :return:
        """
        choice = QuestionChoice(**args)
        db.session.add(choice)
        db.session.commit()
        return choice
    
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
            db.session.add(exam)  # TODO Need to commit to db to generate exam.id
            db.session.commit()
            return exam
        else:
            raise Exception('Invalid arguments. Could not create exam')
    
    def validate(self, csv_rows, args):
        """
        Validates if input is valid. Row should containing the following
        - question
        - Atleast two choices
        - answer
        - allocated_marks
        :return:
        """
        for record in csv_rows:
            question = record.get('question', None)
            answer = record.get('answer', None)
            choices = [{'choice': v, 'is_answer': k == answer} for k, v in record.iteritems() if
                       str(k).startswith('choice')]
            allocated_marks = record.get('allocated_marks', None)
            
            if not question or not answer or not allocated_marks:
                raise Exception('CSV missing required columns')
            
            if len(choices) < 2:
                raise Exception("Atleast two choices required")
            
            if answer not in [k for k, v in record.iteritems() if str(k).startswith('choice')]:
                raise Exception('Invalid answer given')
        
        exam = self.create_exam(args)
        
        for record in csv_rows:
            question = record.get('question', None)
            answer = record.get('answer', None)
            choices = [{'choice': v, 'is_answer': k == answer} for k, v in record.iteritems() if
                       str(k).startswith('choice')]
            allocated_marks = record.get('allocated_marks', None)
            question_obj = self.create_question({
                'question': question,
                'allocated_marks': allocated_marks,
                'batch_id': self.batch_id,
                'country': self.country
            })
            
            for choice in choices:
                self.create_question_choice({
                    'question_id': question_obj.id,
                    'question_choice': choice.get('choice'),
                    'is_answer': choice.get('is_answer', False),
                    'allocated_marks': allocated_marks,
                    'country': self.country
                })
            
            exam_question = ExamQuestion(
                id=None,
                exam_id=exam.id,
                question_id=question_obj.id,
                weight=csv_rows.index(record),
                allocated_marks=question_obj.allocated_marks,
                country=exam.country,
                archived=False
            )
            
            db.session.add(exam_question)
            db.session.commit()
    
    def run(self, csv_rows, title, exam_status_id, passmark, is_certification, certification_type):
        assert isinstance(csv_rows, list), 'Invalid arguments. CSV rows must be a list'
        assert title is not None, "Invalid exam title"
        assert isinstance(is_certification, bool), 'Invalid is certification'
        
        self.validate(csv_rows, {
            'title': title,
            'country': self.country,
            'exam_status_id': exam_status_id,
            'passmark': passmark,
            'certification_type_id': certification_type if is_certification else None
        })
