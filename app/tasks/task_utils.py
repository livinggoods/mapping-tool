from flask import current_app
from abc import ABCMeta, abstractmethod, abstractproperty

from app import db
from app.models import Task, User


class TaskManager:
    """
    Task manager class
    Manages various tasks
    @TODO add a method to kill a task in progress
    """
    def __init__(self, user=None, *args, **kwargs):
        
        if not isinstance(user, User):
            user = None
            
        self.user = user
    
    def launch_task(self, task, description=None, *args, **kwargs):
        """
        Create a new task
        :param task:
        :param description:
        :param args:
        :param kwargs:
        :return:
        """
        rq_job = current_app.task_queue.enqueue(task, *args, **kwargs)
        task = Task(
            id=rq_job.get_id(),
            name=task,
            description=description,
            user_id=self.user.id if self.user else None
        )
        db.session.add(task)
        return task
        
    def get_tasks_in_progress(self):
        """
        Returns a list of all tasks running for @{self.user}.
        If @{self.user} is None, return all running tasks for all users
        :return:
        """
        if self.user:
            return Task.query.filter_by(user_id=self.user.id, complete=False).all()
        else:
            return Task.query.filter_by(complete=False).all()
    
    def get_task_in_progress(self, task):
        """
        Returns task in progress for user if user, else returns latest added task
        :param task:
        :return:
        """
        if self.user:
            return Task.query.filter_by(name=task, user_id=self.user.id, complete=False).first()
        else:
            return Task.query.filter_by(name=task, complete=False).first()
