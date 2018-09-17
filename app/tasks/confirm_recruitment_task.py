import math
import os
import time
import uuid

from app import create_app, db
from app.models import Recruitments, Training, SessionTopic, TrainingSession, TrainingClasses, Trainees, \
    SessionAttendance

application = create_app(os.getenv('FLASK_CONFIG', 'default'))

TRAINEE_PER_CLASS = 35
MAX_DEVIATION_PER_CLASS = 5


class ConfirmRecruitmentTask:
    def __init__(self, recruitment_id=None, task=None, job=None):
        if recruitment_id is None or task is None or job is None:
            raise Exception("Invalid state of the task")
        
        self.recruitment_id = recruitment_id
        self.task = task
        self.job = job
    
    def generate_classes(self, trainees=None):
        """
        Algorithm to generate classes
        :return:
        """
        print("Generating class using algorithm")
        class_details = {}
        class_count = 0
        if trainees is not None:
            trainee_count = len(trainees)
            class_count = int(math.ceil(trainee_count / float(TRAINEE_PER_CLASS)))
            while len(trainees) > 0:
                for i in range(1, class_count + 1, 1):
                    if str(i) not in class_details:
                        class_details[str(i)] = []
                    
                    for j in range(1, i + 1, 1):
                        if len(trainees) > 0:
                            class_details[str(j)].append(trainees[0])
                            trainees.pop(0)
        return {"classes": class_count, 'details': class_details}
    
    def generate_training_classes(self, recruitment):
        """
        Generate the training classes and assign CHV to each class.
        TODO: Improve on this algorithm
        :param recruitment:
        :return:
        """
        # determine the number of classes
        # count the number of items in the __dict__
        # Based on the country, generate the number of classes
        # The classes in each country have a set numnber of trainees.
        print("Generating Training classes ...")
        count = recruitment.get('data').get('count')
        number_of_classes = 1
        class_details = {}
        trainees = recruitment.get('data').get('registrations')
        if recruitment.get('country') == "KE" or recruitment.get('country') == 'UG' or recruitment.get('country') == 'TZ':
            return self.generate_classes(trainees=[trainee.get('id') for trainee in trainees])
        else:
            return {'count': recruitment.get('data').get('count'),
                    'len': len(recruitment.get('data').get('registrations'))}
    
    def create_training(self):
        """
        Creates a new training associated with the recruitment {@self.recruitment_id}
        :return:
        """
        print 'Creating Training....'
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
        """
        Create Training session based on session topics.
        Training session to be used to take attendance
        :param training:
        :return:
        """
        print("Creating Session topics ...")
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
    
    def create_trainee(self, trainee_id=None, new_class=None, training=None, recruitment=None):
        """
        Creates a trainee record
        :param trainee_id:
        :param new_class:
        :param training:
        :param recruitment:
        :return:
        """
        print("Creating Trainee ...")
        if trainee_id is None or new_class is None or training is None or recruitment is None:
            raise Exception("Failed to create trainee ...")
        
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
        
        self.create_training_session(training=training, trainee=trainee)
    
    def create_training_session(self, training=None, trainee=None):
        """
        Create a training session for the a trainee
        :param training:
        :param trainee:
        :return:
        """
        print("Creating Training Session for trainee")
        if training is None or trainee is None:
            raise Exception("Failed to create training sessions")
        
        # Add the trainee to all sessions
        training_sessions_list = TrainingSession.query.filter_by(training_id=training.id, archived=0)
        for session in training_sessions_list:
            sess = SessionAttendance.query.filter_by(trainee_id=trainee.id, training_session_id=session.id,
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
    
    def create_training_class(self, class_details=None, training=None, recruitment=None):
        """
        Create training class
        :param class_details:
        :return:
        """
        print("Creating training classes ...")
        if class_details is None or training is None or recruitment is None:
            print(class_details, training, recruitment)
            raise Exception("Failed to create classes ...")
        
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
                self.create_trainee(trainee_id=trainee_id, new_class=new_class, training=training,
                                    recruitment=recruitment)
    
    def confirm_recruitment(self):
        """
        
        :return:
        """
        print("Confirming Recruitment ...")
        recruitment = Recruitments.query.filter_by(id=self.recruitment_id).first()
        training = self.create_training()
        self.create_training_topics(training)
        
        class_list = self.generate_training_classes(recruitment.to_json())
        # create a class list
        class_details = class_list.get('details')
        self.create_training_class(class_details=class_details, training=training, recruitment=recruitment)
        
        recruitment.status = "confirmed"
        db.session.add(recruitment)
        
        # Task has completed successfully. Delete it.
        db.session.delete(self.task)
        db.session.commit()
    
    def run(self):
        """
        Runs the command
        :return:
        """
        self.confirm_recruitment()
