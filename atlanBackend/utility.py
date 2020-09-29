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
    if resume:
        file_path=path
        task_id=task_id
        task = Tasks.query.filter_by(id=task_id).first()
        task.state = 'PROCESSING'
        db.session.commit()
        
        deleted_r = PausedTasks.__table__.delete().where(PausedTasks.task_id == task_id)
        db.session.execute(deleted_r)
        db.session.commit()
    else:
        file_path = path
        task_id = self.request.id
        print(task_id)
        task = Tasks(id=task_id, operation='Upload', state='PROCESSING', file_path=file_path)
        db.session.add(task)
        db.session.commit()
    
    with open(file_path, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for i in range(start_row+1):
            fields = next(csvreader)

        print("reached celery")
        i=start_row

        for row in csvreader:
            if(AsyncResult(task_id, app=celery).state == 'REVOKED'):
                #delete_rows(task_id)
                print("Task Revoked")
                break
            
            if(AsyncResult(task_id, app=celery).state == 'PAUSED'):
                paused_entry = PausedTasks(task_id=task_id, last_row=i)
                db.session.add(paused_entry)
                db.session.commit()
                task = Tasks.query.filter_by(id=task_id).first()
                task.state = 'PAUSED'
                db.session.commit()
                print("Task Paused")
                break

            if(AsyncResult(task_id, app=celery).state == 'PROCESSING' or AsyncResult(task_id, app=celery).state == 'PENDING'):
                time.sleep(2)
                i=i+1
                print(row)
                csv_entry = CsvEntries(name=row[0], age=row[1], address=row[2],email=row[3], contactNumber=row[4], taskID=task_id)
                db.session.add(csv_entry)
                db.session.commit()
    
        if(AsyncResult(task_id, app=celery).state == 'PROCESSING' or AsyncResult(task_id, app=celery).state == 'PENDING'):
            task = Tasks.query.filter_by(id=task_id).first()
            task.state = 'SUCCESS'
            db.session.commit()
            return 'Uploaded Data!!'




@app.route('/tasks', methods=['GET'])
def tasks():
    res_return=[]
    tasks = Tasks.query.all()
    print(tasks)
    for task in tasks:
        task_dict={'task_id': task.id, 'state': task.state, 'file_path': task.file_path}
        res_return.append(task_dict)    
    return jsonify(results = res_return), 200


@app.route('/terminated_tasks', methods=['GET'])
def terminated_tasks():
    res_return=[]
    tasks = TerminatedTasks.query.all()
    print(tasks)
    for task in tasks:
        task_dict={'task_id': task.task_id}
        res_return.append(task_dict)    
    return jsonify(results = res_return), 200
  
  
@app.route('/paused_tasks', methods=['GET'])
def paused_tasks():
    res_return=[]
    tasks = PausedTasks.query.all()
    print(tasks)
    for task in tasks:
        task_dict={'task_id': task.task_id, 'last_row': task.last_row}
        res_return.append(task_dict)    
    return jsonify(results = res_return), 200
  

@app.route('/csv_entries', methods=['GET'])
def csv_entries():
    res_return=[]
    entries = CsvEntries.query.all()
    print(entries)
    for entry in entries:
        entry_dict={'task_id': entry.taskID, 'name': entry.name,'age': entry.age,'email': entry.email,'address': entry.address}
        res_return.append(entry_dict)    
    return jsonify(results = res_return), 200
  

@app.route('/terminate/<task_id>', methods=['GET'])
def terminate(task_id):
    
    print(AsyncResult(task_id, app=celery).state)
    delete_rows(task_id)
    Task.update_state(self=celery, task_id=task_id, state='REVOKED')
    #revoke(task_id, terminate=True, signal='SIGKILL')
    terminated_entry = TerminatedTasks(task_id=task_id)
    db.session.add(terminated_entry)
    db.session.commit()
    
    task = Tasks.query.filter_by(id=task_id).first()
    task.state = 'REVOKED'
    db.session.commit()
    
    return jsonify({'task_id': task_id, 'status': str(AsyncResult(task_id, app=celery).state)}), 200


@app.route('/pause/<task_id>', methods=['GET'])
def pause(task_id):
    Task.update_state(self=celery, task_id=task_id, state='PAUSED')
    return jsonify({'task_id': task_id, 'status': str(AsyncResult(task_id, app=celery).state)}), 200


@app.route('/resume/<task_id>', methods=['GET'])
def resume_task(task_id):
    Task.update_state(self=celery, task_id=task_id, state='PROCESSING')
    file_path, last_row = get_file_info(task_id)
    csv_upload.delay(path=file_path, start_row=last_row,resume=True, task_id=task_id)
    return jsonify({'task_id': task_id, 'status': 'PROCESSING'}), 200


def delete_rows(task_id):
    deleted_r = CsvEntries.__table__.delete().where(CsvEntries.taskID == task_id)
    db.session.execute(deleted_r)
    db.session.commit()
    

def get_file_info(task_id):
    paused_task=PausedTasks.query.filter_by(task_id=task_id).first()
    last_row=paused_task.last_row
    task=Tasks.query.filter_by(id=task_id).first()
    file_path=task.file_path
    return file_path, last_row
