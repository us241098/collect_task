from celery import Celery
from celery.result import AsyncResult
from celery.exceptions import Ignore
from celery import current_app
from celery.app.task import Task
from celery.task.control import revoke
from io import StringIO
from io import TextIOWrapper
from billiard.exceptions import Terminated
from datetime import datetime
from atlanBackend import app, db, make_celery
from atlanBackend.models import CsvEntries, Tasks, TerminatedTasks, PausedTasks
import time
import csv
from itertools import islice
from flask import Flask, render_template, make_response, \
                request, jsonify, redirect, url_for

celery = make_celery(app)
celery.conf.update(app.config)


@celery.task(bind=True, throws=(Terminated,))
def csv_upload(self, path, start_row=0, resume=False, task_id=0):
    '''
    Writes the CSV lines to DB, also updates the Tasks tables with new tasks and updates the async states according to the API requests.

            Parameters:
                    task_id (string): id of the task to be resumed (only needed to resume a paused task)
                    path (string): path to the CSV file 
                    start_row (int): Row Number of CSV from where to start import (0 unless the task state is being resumed)
                    resume (bool): Flag to check if the task is to be resumed or it is a new task

            Returns:
                    "Uplaoded Data!!": If all the rows are written succesfully
    '''
    
    if resume:                  # Check if the task is being resumed
        file_path=path
        task_id=task_id
        task = Tasks.query.filter_by(id=task_id).first()
        task.state = 'PROCESSING' # change state of paused task to processing
        db.session.commit() 
        
        deleted_r = PausedTasks.__table__.delete().where(PausedTasks.task_id == task_id) # remove from the PausedTask table
        db.session.execute(deleted_r)
        db.session.commit()
    else:                          # task is new
        file_path = path
        task_id = self.request.id  # assign a task_id to the new task
        print(task_id)
        task = Tasks(id=task_id, operation='Upload', state='PROCESSING', file_path=file_path) # add the task to the Tasks table
        db.session.add(task)
        db.session.commit()
    
    with open(file_path, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        
        for i in range(start_row+1): # skip start_row number of lines (0 if task is new otherwise some value if task is being resumed from paused state)
            fields = next(csvreader)

        print("reached celery")      # debug statement
        i=start_row

        for row in csvreader:        # iterate in CSV file
            if(AsyncResult(task_id, app=celery).state == 'REVOKED'):
                print("Task Revoked")
                break
            
            if(AsyncResult(task_id, app=celery).state == 'PAUSED'): # if task is PAUSED add it to the PausedTasks table and update its state in Tasks table
                paused_entry = PausedTasks(task_id=task_id, last_row=i)
                db.session.add(paused_entry)
                db.session.commit()
                task = Tasks.query.filter_by(id=task_id).first()
                task.state = 'PAUSED'
                db.session.commit()
                print("Task Paused")
                break

            if(AsyncResult(task_id, app=celery).state == 'PROCESSING' or AsyncResult(task_id, app=celery).state == 'PENDING'): # if task state is PROCESSING then write entries to the CsvEntries table
                time.sleep(2)
                i=i+1
                print(row)
                csv_entry = CsvEntries(name=row[0], age=row[1], address=row[2],email=row[3], contactNumber=row[4], taskID=task_id)
                db.session.add(csv_entry)
                db.session.commit()
    
        if(AsyncResult(task_id, app=celery).state == 'PROCESSING' or AsyncResult(task_id, app=celery).state == 'PENDING'):
            task = Tasks.query.filter_by(id=task_id).first()
            task.state = 'SUCCESS'  # Update task state to SUCCESS when all rows are successfully written
            db.session.commit()
            return 'Uploaded Data!!'


def delete_rows(task_id):
    '''
    Deletes the rows from CsvEntries made by task of task_id
            Parameters:
                    task_id (string): id of the task of which entries are to be deleted
    '''
    
    deleted_r = CsvEntries.__table__.delete().where(CsvEntries.taskID == task_id)
    db.session.execute(deleted_r)
    db.session.commit()
    

def get_file_info(task_id):
    '''
    Returns file_path and last row written given the id of the PAUSED task
            Parameters:
                    task_id (string): id of the PAUSED task
            Returns:
                    file_path (string): path to the file uploaded in task
                    last_row (int): last row executed before the task was stopped
    '''
    
    paused_task=PausedTasks.query.filter_by(task_id=task_id).first()
    last_row=paused_task.last_row
    task=Tasks.query.filter_by(id=task_id).first()
    file_path=task.file_path
    return file_path, last_row
