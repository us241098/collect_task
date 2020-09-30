from flask import request, jsonify, json
from atlanBackend import app, db, make_celery
from io import TextIOWrapper
from celery.result import AsyncResult
from celery.exceptions import Ignore
from celery import current_app
from celery.app.task import Task
import os
from atlanBackend.utility import csv_upload, delete_rows, get_file_info, celery
from werkzeug.utils import secure_filename
from flask import Flask, render_template, make_response, request, jsonify, redirect, url_for
from atlanBackend.models import CsvEntries, Tasks, TerminatedTasks, PausedTasks


# endpoint to upload CSV and start import
@app.route('/', methods=['GET', 'POST'])
def uploadd_csv():
    if request.method == 'POST':
        _file = request.files['file']
        filename = secure_filename(_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        _file.save(file_path)
        # Task sent to celery worker
        csv_upload.delay(file_path)
        #return jsonify({}), 201
        return redirect(url_for('uploadd_csv'))
    return """
            <form method='post' action='/' enctype='multipart/form-data'>
              Upload a csv file: <input type='file' name='file'>
              <input type='submit' value='Upload'>
            </form>
           """


# endpoint to list all the tasks
@app.route('/tasks', methods=['GET'])
def tasks():
    res_return=[]
    tasks = Tasks.query.all()
    print(tasks)
    for task in tasks:
        task_dict={'task_id': task.id, 'state': task.state, 'file_path': task.file_path}
        res_return.append(task_dict)    
    return jsonify(results = res_return), 200


# endpoint to list terminated tasks
@app.route('/terminated_tasks', methods=['GET'])
def terminated_tasks():
    res_return=[]
    tasks = TerminatedTasks.query.all()
    print(tasks)
    for task in tasks:
        task_dict={'task_id': task.task_id}
        res_return.append(task_dict)    
    return jsonify(results = res_return), 200

  
# endpoint to list paused tasks
@app.route('/paused_tasks', methods=['GET'])
def paused_tasks():
    res_return=[]
    tasks = PausedTasks.query.all()
    print(tasks)
    for task in tasks:
        task_dict={'task_id': task.task_id, 'last_row': task.last_row}
        res_return.append(task_dict)    
    return jsonify(results = res_return), 200

  
# endpoint to list CSV entries in Database
@app.route('/csv_entries', methods=['GET'])
def csv_entries():
    res_return=[]
    entries = CsvEntries.query.all()
    print(entries)
    for entry in entries:
        entry_dict={'task_id': entry.taskID, 'name': entry.name,'age': entry.age,'email': entry.email,'address': entry.address}
        res_return.append(entry_dict)    
    return jsonify(results = res_return), 200

  
# Terminates the task of given id
@app.route('/terminate/<task_id>', methods=['GET'])
def terminate(task_id):
    print(AsyncResult(task_id, app=celery).state)
    delete_rows(task_id)
    Task.update_state(self=celery, task_id=task_id, state='REVOKED')
    terminated_entry = TerminatedTasks(task_id=task_id)
    db.session.add(terminated_entry)
    db.session.commit()
    task = Tasks.query.filter_by(id=task_id).first()
    task.state = 'REVOKED'
    db.session.commit()
    return jsonify({'task_id': task_id, 'status': str(AsyncResult(task_id, app=celery).state)}), 200


# Pauses the task of given id
@app.route('/pause/<task_id>', methods=['GET'])
def pause(task_id):
    Task.update_state(self=celery, task_id=task_id, state='PAUSED')
    return jsonify({'task_id': task_id, 'status': str(AsyncResult(task_id, app=celery).state)}), 200


# Resumes the task of given id
@app.route('/resume/<task_id>', methods=['GET'])
def resume_task(task_id):
    Task.update_state(self=celery, task_id=task_id, state='PROCESSING')
    file_path, last_row = get_file_info(task_id)
    csv_upload.delay(path=file_path, start_row=last_row,resume=True, task_id=task_id)
    return jsonify({'task_id': task_id, 'status': 'PROCESSING'}), 200


