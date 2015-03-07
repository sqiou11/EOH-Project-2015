from flask import Flask, make_response, request, render_template, session, redirect, url_for, escape, g, send_from_directory
import sqlite3, os
from werkzeug import secure_filename
from GPSFromExif import get_lat_lon, get_exif_data
from PIL import Image
import geojson, json
from ImageHandler import mergeSort

app = Flask(__name__)

DATABASE = '/home/sqiou11/Documents/EOH-Project-2015/eoh_2015.db'
IMAGE_FOLDER = '/home/sqiou11/Documents/EOH-Project-2015/images'
GEOJSON_FOLDER = '/home/sqiou11/Documents/EOH-Project-2015/maps'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'html'])

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

@app.route('/index')
def index():
	if 'name' in session:
		return render_template("index.html", name=escape(session['name']), username=escape(session['username']))
	return render_template("index.html")

@app.route('/register')
def register():
	return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		user = query_db('select * from users where username = ?', [request.form['username']], one=True)
		if user != None:
			if user['password'] == request.form['password']:
				session['name'] = user['firstName'] + ' ' + user['lastName']
				session['username'] = user['username']
				return redirect(url_for('index'))
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
		return render_template('userMain.html', name=escape(session['name']), username=escape(session['username']), maps=saved_maps)
	return redirect(url_for('login'))

# Route that will process the file upload and generate GeoJSON data for the created map
@app.route('/users/<username>/upload', methods=['POST'])
def upload(username):
    # Get the name of the uploaded files
    uploaded_files = request.files.getlist("file[]")
    image_locations = []
    features = []
    lineString_coords = []
    for file in uploaded_files:
        # Check if the file is one of the allowed types/extensions
        if file and allowed_file(file.filename):
            # Make the filename safe, remove unsupported chars
            filename = secure_filename(file.filename)
            # Move the file form the temporal folder to the upload
            # folder we setup
            location = os.path.join(app.config['IMAGE_FOLDER'], filename)
            file.save(location)

            #prevent duplicate inserts by first checking if an identical record exists (same username, map name, and location)
            prevUpload = query_db('select * from images where username = ? and mapName = ? and fileName = ?', [username, request.form['mapName'], filename], one=True)
            if not prevUpload:
            	insert('images', ['username', 'mapName', 'fileName', 'fileLocation'], [username, request.form['mapName'], filename, location])

            image_locations.append(location)

    image_locations = mergeSort(image_locations)
    for loc in image_locations:
    	img = Image.open(loc)
    	coords = get_lat_lon(get_exif_data(img))
    	if coords.count(None) != len(coords):
    		point = geojson.Point(coords)
    		features.append(geojson.Feature(geometry=point, properties={ 'image': loc[len(app.config['IMAGE_FOLDER'])+1:] }))
    		#add each coord to our Line that will connect them all
    		lineString_coords.append(coords)

    features.append(geojson.Feature(geometry=geojson.LineString(lineString_coords)))

    #create featureCollection obj with the feature array we made
    featureCollection = geojson.FeatureCollection(features)
    geojson_file_name = username + '_' + request.form['mapName'] + '.json'
    geojson_file_path = str(app.config['GEOJSON_FOLDER'] + '/' + geojson_file_name)
    with open(geojson_file_path, 'w') as outfile:
    	json.dump(featureCollection, outfile, indent=4)
    outfile.close()

    currMap = query_db('select * from maps where username = ? and mapName = ?', [username, request.form['mapName']], one=True)
    if not currMap:
    	insert('maps', ['username', 'mapName', 'fileName', 'fileLocation'], [username, request.form['mapName'], geojson_file_name, geojson_file_path])

    #redirect user to map displaying their goods
    return redirect(url_for('display_map', username=username, mapName=request.form['mapName']))

@app.route('/users/<username>/maps/<mapName>')
def display_map(username, mapName):
	mapCursor = query_db('select * from maps where username = ? and mapName = ?', [username, mapName], one=True)
	print mapCursor
	return render_template('map.html', username=username, mapName=mapName, geoJSONFile=mapCursor['fileName'])

#urls used to retrieve images and geojson files
@app.route('/users/<username>/geojson/<filename>')
def get_geojson_file(username, filename):
	return send_from_directory(app.config['GEOJSON_FOLDER'], filename)

@app.route('/users/<username>/images/<filename>')
def get_image(username, filename):
	return send_from_directory(app.config['IMAGE_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug = True)