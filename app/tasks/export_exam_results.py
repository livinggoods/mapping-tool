from app.models import Training, TrainingExam, ExamResult, Question, Trainees, Registration
from flask.ext import excel

class Memoize:
    def __init__(self, fn):
        self.fn = fn
        self.memo = {}

    def __call__(self, *args):
        if args not in self.memo:
            self.memo[args] = self.fn(*args)
        return self.memo[args]
    

class ExportExamResults():
    TITLES = [
        'Exam Title',
        "Is Certification",
        'Exam Database ID',
        "Training Exam Database ID",
        "Exam Passmark",
        "Exam Unlock Code",
        "Trainee Name",
        "Recruitment ID",
        "Trainee ID",
        'question_title',
        'question_id',
        'answer_selected',
        'answer_choice_id',
        'Is correct',
        "Question Score"
    ]
    
    def __init__(self, training, training_exam):
        assert isinstance(training, Training), 'Invalid Training arguments'
        assert isinstance(training_exam, TrainingExam), 'Invalid Training Exam argument'
        
        self.training = training
        self.training_exam = training_exam

    @staticmethod
    @Memoize
    def get_exam(training_exam_id):
        training_exam = TrainingExam.query.filter_by(id=training_exam_id).first()
        return [
            training_exam.exam.title,
            "Yes" if training_exam.exam.certification_type_id else "No",
            training_exam.exam.id,
            training_exam.id,
            training_exam.passmark,
            training_exam.unlock_code
        ]

    @staticmethod
    @Memoize
    def get_question(question_id):
        question = Question.query.filter_by(id=question_id).first()
        return [
            question.question,
            question.id
        ]

    @staticmethod
    @Memoize
    def get_trainee(trainee_id):
        trainee = Trainees.query.filter_by(id=trainee_id).first()
    
        return [
            trainee.registration.name,
            trainee.registration.id,
            trainee_id
        ]
    
    def run(self):
        exam_results = ExamResult.query.filter_by(training_exam_id=self.training_exam.id)
        data = list()
        data.append(self.TITLES)
        for result in exam_results:
            datum = []
            datum.extend(ExportExamResults.get_exam(result.training_exam_id))
            datum.extend(ExportExamResults.get_trainee(result.trainee_id))
            datum.extend(ExportExamResults.get_question(result.question_id))
            datum.append(result.answer)
            datum.append(result.choice_id)
            datum.append('wrong' if result.question_score == 0 else 'correct')
            datum.append(result.question_score)
            
            data.append(datum)
        output = excel.make_response_from_array(data, 'csv')
        output.headers["Content-Disposition"] = "attachment; filename={}-{}-results.csv".format(self.training.training_name, self.training_exam.exam.title)
        output.headers["Content-type"] = "text/csv"
        return output