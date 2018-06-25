from .. import db
from ..models import *
from .. data import data
from flask import current_app


def exam_with_questions_to_dict(exam):
  result = asdict(exam)
  if not result.has_key('exam_status'):
    result['exam_status'] = exam.exam_status.to_json() if exam.exam_status else None
  
  if not result.has_key('questions'):
    questions = []
    exam_questions = ExamQuestion.query.filter_by(exam_id=exam.id, archived=False).order_by(ExamQuestion.weight)
    for question in exam_questions:
      question_as_dict_ = question.question._asdict()
      question_as_dict_['allocated_marks'] = question.question.allocated_marks \
        if question.allocated_marks is None else question.allocated_marks
      questions.append(question_as_dict_)
    
    result["questions"] = questions
  
  return result