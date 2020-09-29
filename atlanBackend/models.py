from atlanBackend import db
from flask import Flask

# User Model Definition
class CsvEntries(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    taskID = db.Column(db.Integer, db.ForeignKey('tasks.id'), index=True)
    name = db.Column(db.String(64), index=True)
    age = db.Column(db.Integer)
    contactNumber = db.Column(db.String(20))
    email = db.Column(db.String(120), index=True)
    address = db.Column(db.String(300))

    def __repr__(self):
        return '<User {}>'.format(self.id)

class Tasks(db.Model):
    id = db.Column(db.String(40), primary_key=True)
    operation = db.Column(db.String(30), index=True)
    state = db.Column(db.String(30), index=True)
    user = db.relationship('CsvEntries', backref='tasks', lazy='dynamic')
    file_path = db.Column(db.String(120), index=True)

    def __repr__(self):
        return '<Task {}>'.format(self.id)

    
    
# RevokedTask Model Definition
class TerminatedTasks(db.Model):
    task_id = db.Column(db.String(36), primary_key=True)
    # Getting the string representation of model on querying
    def __repr__(self):
        return '<Revoked Tasks {}>'.format(self.task_id)
    
# PausedTask Model Definition
class PausedTasks(db.Model):
    task_id = db.Column(db.String(36), primary_key=True)
    last_row = db.Column(db.Integer)
    # Getting the string representation of model on querying
    def __repr__(self):
        return '<Paused Tasks {}>'.format(self.task_id)
    
db.create_all()