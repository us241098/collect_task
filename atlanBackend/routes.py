from flask import request, jsonify, json
from atlanBackend import app
from io import TextIOWrapper

import os
from atlanBackend.utility import csv_upload
from werkzeug.utils import secure_filename
from flask import Flask, render_template, make_response, \
                request, jsonify, redirect, url_for



@app.route('/', methods=['GET', 'POST'])
def uploadd_csv():
    if request.method == 'POST':
        _file = request.files['file']
        filename = secure_filename(_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        _file.save(file_path)
        # Sending task to celery worker
        csv_upload.delay(file_path)
        #return jsonify({}), 201
        return redirect(url_for('uploadd_csv'))
    return """
            <form method='post' action='/' enctype='multipart/form-data'>
              Upload a csv file: <input type='file' name='file'>
              <input type='submit' value='Upload'>
            </form>
           """
           



