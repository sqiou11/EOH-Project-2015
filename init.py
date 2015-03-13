from flask import Flask, make_response, request, render_template, session, redirect, url_for, escape, g, send_from_directory
import sqlite3, os
from werkzeug import secure_filename
from GPSFromExif import get_lat_lon, get_exif_data
from PIL import Image
import geojson, json, shutil, time
from ImageHandler import mergeSort
from bson.json_util import dumps

app = Flask(__name__)

DATABASE = '/home/sqiou11/Documents/EOH-Project-2015/eoh_2015.db'
IMAGE_FOLDER = '/home/sqiou11/Documents/EOH-Project-2015/images'
GEOJSON_FOLDER = '/home/sqiou11/Documents/EOH-Project-2015/maps'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'txt'])
TIME_FORMAT = '%Y:%m:%d %H:%M:%S'
EDA_INTERVAL_SECONDS = 20

app.secret_key = 'F12Zr47j\3yX R~X@H!jmM]Lwf/,?KT'
app.config['IMAGE_FOLDER'] = IMAGE_FOLDER
app.config['GEOJSON_FOLDER'] = GEOJSON_FOLDER

#ALL DATABASE FUNCTIONS
def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    db = get_db()
    db.row_factory = make_dicts
    cur = db.execute(query, args)
    db.commit()
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def insert(table, fields=(), values=()):
	db = get_db()
	cur = db.cursor()
	query = 'INSERT OR REPLACE INTO %s (%s) VALUES (%s)' % (table, ', '.join(fields), ', '.join(['?'] * len(values)))
	cur.execute(query, values)
	db.commit()
	id = cur.lastrowid
	cur.close()
	return id

#ALL APP FUNCTIONS
@app.route('/')
def cover():
    return render_template("cover.html")

#index page
@app.route('/index')
def index():
	if 'name' in session:
		return render_template("index.html", name=escape(session['name']), username=escape(session['username']))
	return render_template("index.html")

#project page
@app.route('/project')
def project():
    if 'name' in session:
        return render_template("project.html", name=escape(session['name']), username=escape(session['username']))
    return render_template("project.html")

#register page
@app.route('/register')
def register():
	return render_template("register.html")

#login page
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		user = query_db('select * from users where username = ?', [request.form['username']], one=True)
		if user != None:
			if user['password'] == request.form['password']:
				session['name'] = user['firstName'] + ' ' + user['lastName']
				session['username'] = user['username']
				return redirect(url_for('userMainPage', username=session['username']))
			return render_template('login.html', errorMsg = 'Invalid username or password')
		return render_template('login.html', errorMsg = 'Invalid username or password')
	return render_template("login.html")

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('name', None)
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/users/<username>')
def userMainPage(username):
	if 'username' in session and escape(session['username']) == username:
		saved_maps = query_db('select * from maps where username = ?', [username], one=False)
		return render_template('userMain.html', name=escape(session['name']), username=escape(session['username']), maps=saved_maps, mapString=dumps(saved_maps))
	return redirect(url_for('login'))

# Route that will process the file upload and generate GeoJSON data for the created map
@app.route('/users/<username>/upload', methods=['POST'])
def upload(username):
    # Get the name of the uploaded files
    uploaded_files = request.files.getlist("file[]")
    image_locations = []
    features = []
    lineString_coords = []

    folder = str(app.config['IMAGE_FOLDER'] + '/' + username + '/' + request.form['mapName'])
    #if user's map folder exists, delete it
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)
    query_db('delete from images where username = ? and mapName = ?', [username, request.form['mapName']])
    query_db('delete from maps where username = ? and mapName = ?', [username, request.form['mapName']])

    for file in uploaded_files:
        # Check if the file is one of the allowed types/extensions
        if file and allowed_file(file.filename):
            # Make the filename safe, remove unsupported chars
            filename = secure_filename(file.filename)
            # Move the file form the temporal folder to the upload
            # folder we setup
            
            location = os.path.join(folder, filename)
            file.save(location)

            #prevent duplicate inserts by first checking if an identical record exists (same username, map name, and location)
            insert('images', ['username', 'mapName', 'fileName', 'fileLocation'], [username, request.form['mapName'], filename, location])

            image_locations.append(location)

    #extract EDA data from the EDA file
    edaFile = request.files["edaPeakFile"]
    sensorFile = request.files['sensorFile']
    peakTimes = []
    lineCounter = 0
    startTime = time.strptime("2015:03:06 15:38:13", TIME_FORMAT)
    for line in edaFile:
        if lineCounter != 0:
            #get the peakTime from the row and store it as total time (startTime + peakTime)
            peakTimes.append(float(time.mktime(startTime)) + float(line.split('\t')[1]))
        lineCounter += 1

    if len(image_locations) != 0:
        image_locations = mergeSort(image_locations)
    image_id = 1
    prevCoords = (None, None)


    #ideally iterate through the gps coordinates instead of the pictures, but iterate through pictures for now
    for loc in image_locations:
    	img = Image.open(loc)
    	exif = get_exif_data(img)
    	coords = get_lat_lon(exif)
        #if image exif contains gps coords
    	if coords.count(None) != len(coords):
            point = geojson.Point(coords)
            image_time = time.strptime(exif['DateTime'], TIME_FORMAT)
            peakTimeIndex = 0
            peakTimeCount = 0

            #only traverse the array up to when the peakTime is beyond the image timestamp + 3 seconds
            while peakTimeIndex < len(peakTimes) and peakTimes[peakTimeIndex] <= float(time.mktime(image_time)) + EDA_INTERVAL_SECONDS:
                if peakTimes[peakTimeIndex] >= float(time.mktime(image_time)):
                    peakTimeCount += 1
                peakTimeIndex += 1

            features.append(geojson.Feature(geometry=point, id=image_id, properties={ 'image': loc[len(app.config['IMAGE_FOLDER'])+1:], 'timestamp': exif['DateTime'], 'gps': coords, 'orientation': exif['Orientation'], 'peaksPerSecond': float(peakTimeCount)/EDA_INTERVAL_SECONDS }))
    		#if there was a previous point, create a line connecting this point with the previous point
            if prevCoords.count(None) != len(coords):
    			features.append(geojson.Feature(geometry=geojson.LineString([prevCoords, coords]), properties={ 'average': None}))
            prevCoords = coords
            image_id += 1

    #create featureCollection obj with the feature array we made and write it all to a file
    featureCollection = geojson.FeatureCollection(features)
    geojson_file_name = request.form['mapName'] + '.json'
    geojson_file_folder = str(app.config['GEOJSON_FOLDER'] + '/' + username + '/' + request.form['mapName'])

    #clean out data file directory for this map and replace it
    if os.path.exists(geojson_file_folder):
        shutil.rmtree(geojson_file_folder)
    os.makedirs(geojson_file_folder)
    geojson_file_path = os.path.join(geojson_file_folder, geojson_file_name)

    with open(geojson_file_path, 'w') as outfile:
    	json.dump(featureCollection, outfile, indent=4)
    outfile.close()

    insert('maps', ['username', 'mapName', 'fileName', 'fileLocation'], [username, request.form['mapName'], geojson_file_name, geojson_file_path])

    sensorFile.save(os.path.join(geojson_file_folder, 'EDA_GPS.txt'))

    #redirect user to map displaying their goods
    return redirect(url_for('display_map', username=username, mapName=request.form['mapName']))

@app.route('/users/<username>/maps/<mapName>')
def display_map(username, mapName):
	mapCursor = query_db('select * from maps where username = ? and mapName = ?', [username, mapName], one=True)
	return render_template('map.html', username=username, mapName=mapName, geoJSONFile=mapCursor['fileName'])

#urls used to retrieve images and geojson files
@app.route('/geojson/<username>/<mapName>/<filename>')
def get_geojson_file(username, mapName, filename):
	return send_from_directory(app.config['GEOJSON_FOLDER'] + '/' + username + '/' + mapName, filename)

@app.route('/images/<username>/<mapName>/<filename>')
def get_image(username, mapName, filename):
	return send_from_directory(app.config['IMAGE_FOLDER'] + '/' + username + '/' + mapName, filename)

@app.route('/delete/<username>/<mapName>')
def delete_map(username, mapName):
    #delete the actual folder and all its contents
    folder = str(app.config['IMAGE_FOLDER'] + '/' + username + '/' + mapName)
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.remove(str(app.config['GEOJSON_FOLDER'] + '/' + username + '/' + mapName + '/' + mapName + '.json'))
    #delete all image records associated with that map
    query_db('delete from images where username = ? and mapName = ?', [username, mapName])
    #delete map record from db as well
    query_db('delete from maps where username = ? and mapName = ?', [username, mapName])
    return redirect(url_for('userMainPage', username=username))

@app.route('/edagraph/<username>/<mapName>')
def getEDAGraphValues(username, mapName):
    edaFile = open(app.config['GEOJSON_FOLDER'] + '/' + username + '/' + mapName + '/EDA_GPS.txt', 'r')
    coords = []
    lineCounter = -1
    for line in edaFile:
        if lineCounter != -1:
            coords.append( {'x': line.split('\t')[0], 'y': line.split('\t')[1]} ) #append objects of lineCounter(essentially the "time" elapsed instead of 0-15 repeatedly) and EDA readings
        lineCounter += 1
    return json.dumps(coords)

@app.route('/edapeakvalley/<username>/<mapName>')
def getEDAPeakValley(username, mapName):
    peakValleyFile = open(app.config['GEOJSON_FOLDER'] + '/' + username + '/' + mapName + '/EDA_PV.txt', 'r')
    peakValleyObj = {}
    peakValleyObj['peaks'] = []
    peakValleyObj['valleys'] = []
    lineCounter = -1
    for line in peakValleyFile:
        if lineCounter != -1:
            peakValleyObj['valleys'].append(line.split('\t')[0])
            peakValleyObj['peaks'].append(line.split('\t')[1])
        lineCounter += 1

    return json.dumps(peakValleyObj)

if __name__ == "__main__":
    app.run(debug = True)