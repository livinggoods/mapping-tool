import os
from app import create_app, db
application = create_app(os.getenv('FLASK_CONFIG', 'default'))
from app.models import *

class confirmRecruitment:
  
  def __init__(self, recruitment_id):
    self.recruitment_id = recruitment_id
    
  def generate_training_classes(self, recruitment):
    # determine the number of classes
    # count the number of items in the __dict__
    # Based on the country, generate the number of classes
    # The classes in each country have a set numnber of trainees.
    count = recruitment.get('data').get('count')
    number_of_classes = 1
    class_details = {}
    trainees = recruitment.get('data').get('registrations')
    if recruitment.get('country') == "KE" or recruitment.get('country') == 'UG':
      if count <= 35:
        if len(trainees) > 0:
          class_details[1] = [trainee.get('id') for trainee in trainees]
      elif count > 35 and count <= 70:
        number_of_classes = 2
        class_1 = []
        class_2 = []
        x = 1
        for trainee in trainees:
          if x == 1:
            class_1.append(trainee.get('id'))
            x += 1
          elif x == 2:
            class_2.append(trainee.get('id'))
            x = 1
        class_details[1] = class_1
        class_details[2] = class_2
      elif count > 70 and count <= 110:
        number_of_classes = 3
        class_1 = []
        class_2 = []
        class_3 = []
        x = 1
        for trainee in trainees:
          if x == 1:
            class_1.append(trainee.get('id'))
            x += 1
          elif x == 2:
            class_2.append(trainee.get('id'))
            x += 1
          else:
            class_3.append(trainee.get('id'))
            x = 1
        class_details[1] = class_1
        class_details[2] = class_2
        class_details[3] = class_3
      return {"classes": number_of_classes, 'details': class_details}
    else:
      return {'count': recruitment.get('data').get('count'), 'len': len(recruitment.get('data').get('registrations'))}

  def create_training(self):
    print '*-'*20
    recruitment = Recruitments.query.filter_by(id=self.recruitment_id).first()
    training = Training.query.filter_by(recruitment_id=self.recruitment_id).first()
    if not training:
      training = Training(
          id=str(uuid.uuid4()),
          training_name=recruitment.name,
          country=recruitment.country,
          district=recruitment.district,
          recruitment_id=recruitment.id,
          training_status_id=1,
          client_time=time.time(),
      )
      if recruitment.country == 'KE':
        if recruitment.subcounty_id is not None:
          training.subcounty_id = recruitment.subcounty_id
        if recruitment.county_id is not None:
          training.county_id = recruitment.county_id
      else:
        if recruitment.location_id is not None:
          training.location_id = recruitment.location_id
    db.session.add(training)
    db.session.commit()
    return training

  def create_training_topics(self, training):
    session_topics = SessionTopic.query.filter_by(country=training.country, archived=0)
    for topic in session_topics:
      training_session = TrainingSession.query.filter_by(country=training.country, training_id=training.id,
                                                         session_topic_id=topic.id, archived=0).first()
      if not training_session:
        training_session = TrainingSession(
            id=str(uuid.uuid4()),
            training_id=training.id,
            session_topic_id=topic.id,
            country=training.country,
            created_by=1
        )
      db.session.add(training_session)
      db.session.commit()

  def confirm_recruitment(self):
    recruitment  = Recruitments.query.filter_by(id=self.recruitment_id).first()
    training = self.create_training()
    self.create_training_topics(training)
  
    class_list = self.generate_training_classes(recruitment.to_json())
    # create a class list
    class_details = class_list.get('details')
    for k, v in class_details.iteritems():
      # class is k, trainees = v
      new_class = TrainingClasses.query.filter_by(training_id=str(training.id), class_name=str(k)).first()
      if not new_class:
        new_class = TrainingClasses(
            training_id=training.id,
            class_name=k,
            created_by=1,
            client_time=int(time.time()),
            date_created=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            country=recruitment.country
        )
        db.session.add(new_class)
        db.session.commit()
      #   Create trainees
      for trainee_id in v:
        trainee = Trainees.query.filter_by(id=trainee_id).first()
        if not trainee:
          trainee = Trainees(
              id=trainee_id,
              registration_id=trainee_id,
              class_id=new_class.id,
              training_id=training.id,
              country=recruitment.country,
              date_created=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
              added_by=1,
              client_time=int(time.time()),
          )
          db.session.add(trainee)
          db.session.commit()
        # Add the trainee to some sessions
        training_sessions_list = TrainingSession.query.filter_by(training_id=training.id, archived=0)
        for session in training_sessions_list:
          sess = SessionAttendance.query.filter_by(trainee_id=trainee_id, training_session_id=session.id,
                                                   training_id=training.id).first()
          if not sess:
            sess = SessionAttendance(
                id=str(uuid.uuid4())
            )
          sess.training_session_id = session.id
          sess.trainee_id = trainee.id
          sess.training_id = training.id
          sess.country = training.country
          sess.client_time = int(time.time())
          sess.date_created = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
          db.session.add(sess)
          db.session.commit()
  
    # create / generate Sessions
    # TrainingSessiions, needs to have a training_topic
    # @TODO  create initial 3 training_sessions
  
    #   Create default Trainee attendances here, we export this to the App

