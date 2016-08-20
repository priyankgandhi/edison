import os, json
import bmo_offers_generic_converter as bmo
from flask import Flask, flash, request, redirect, url_for, render_template,  send_from_directory
from werkzeug.utils import secure_filename
from flask.ext.cache import Cache


UPLOAD_FOLDER = '/tmp/'
DOWNLOAD_FOLDER = '/tmp/'
ALLOWED_EXTENSIONS = set(['csv'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
cache = Cache(app,config={'CACHE_TYPE': 'simple'})

def allowed_file(filename):
    return '.' in filename and \
    	filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename) 
            file.save(filepath)
            response = bmo.convert(filepath, app.config['DOWNLOAD_FOLDER'])
            cache.set(filename, response)
            #return redirect(url_for('uploaded_file', filename=filename))
            return redirect(url_for('status', filename=filename))
        else:
        	flash('Invalid file extension. Allowed Extensions: ' + ",".join(ALLOWED_EXTENSIONS))
        	return redirect(request.url)
    return render_template('index.html')

@app.route('/status/<filename>')
def status(filename):
	response_str = cache.get(filename)
	try:
		response = json.loads(response_str)
	except:
		response = {}
	summary = '\n'.join(response.get('summary', ''))
	failures = response.get('failures',None)	
	return render_template('status.html', response=response, summary=summary, failures=failures, filename=filename)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

if __name__ == "__main__":
	app.secret_key = 'super secret key is here'
	app.config['SESSION_TYPE'] = '/tmp'
	app.run(host="0.0.0.0", debug=True)
