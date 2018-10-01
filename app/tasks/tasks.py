import os
import time

import rq

from app import create_app, db
from app.models import Training, Task
from app.tasks.confirm_recruitment_task import ConfirmRecruitmentTask
from app.tasks.sync_parish_task import SyncParishTask
from app.tasks.sync_villages_task import SyncVillagesTask

app = create_app(os.getenv('FLASK_CONFIG', 'default'))
app.app_context().push()


def example_task(seconds=2000):
    job = rq.get_current_job()
    task = Task.query.filter_by(id=job.id).first()
    trainings = Training.query.all()
    print("trainings", len(trainings))
    
    print('Starting task')
    for i in range(seconds):
        job.meta['progress'] = 100.0 * i / seconds
        job.save_meta()
        print i
        time.sleep(1)
    job.meta['progress'] = 100
    job.save_meta()
    print('Task completed', task)
    task.complete = True
    db.session.merge(task)
    db.session.commit()


def confirm_recruitment_task(recruitment_id=None):
    job = rq.get_current_job()
    task = Task.query.filter_by(id=job.id).first()
    ConfirmRecruitmentTask(recruitment_id=recruitment_id, task=task, job=job).run()
