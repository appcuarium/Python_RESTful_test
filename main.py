#!flask/bin/python
import itertools
import json
import sys

import numpy
import pandas as pd
from bson.objectid import ObjectId
from flask import Flask
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask_httpauth import HTTPBasicAuth
from flask_pymongo import PyMongo
from marshmallow import ValidationError
from werkzeug.security import generate_password_hash, check_password_hash

from schemas.user import UserSchema

app = Flask(__name__, static_url_path="")
auth = HTTPBasicAuth()

app.config['MONGO_DBNAME'] = 'restdb'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/prtdb'
app.testing = 'unittest' in sys.modules.keys()
app.secret_key = '1234_abracadabra'  # Not to be used in production
mongo_mgr = PyMongo(app)


@auth.verify_password
def verify_password(username, password):
    users = mongo_mgr.db.users
    login_user = users.find_one({'username': username})

    if login_user:
        return check_password_hash(login_user['password'], password)

    return False


@auth.error_handler
def unauthorized():
    # return 403 instead of 401 to prevent browsers from displaying the default
    # auth dialog
    return make_response(jsonify({'error': 'Unauthorized access'}), 403)


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/prt/api/v1.0/users', methods=['GET'])
@auth.login_required
def get_users():
    """
    Update this to return a json stream defining a listing of the users
    Note: Always return the appropriate response for the action requested.
    """
    schema = UserSchema()
    response = dict(errors=dict(), results=dict())

    users = mongo_mgr.db.users
    login_user = users.find()

    results = schema.dump(login_user, many=True)
    response['results'] = results.data

    return jsonify(response)


@app.route('/prt/api/v1.0/users/<string:user_id>', methods=['GET'])
@auth.login_required
def get_user(user_id):
    schema = UserSchema()
    response = dict(errors=dict(), results=dict())

    users = mongo_mgr.db.users
    login_user = users.find_one({'_id': ObjectId(user_id)})

    results = schema.dump(login_user)
    response['results'] = results.data

    return jsonify(response)


@app.route('/prt/api/v1.0/users', methods=['POST'])
@auth.login_required
def create_user():
    """
    Should add a new user to the users collection, with validation
    note: Always return the appropriate response for the action requested.
    """
    req = request.form or request.get_json()

    return json.dumps(new_user(req))


@app.route('/prt/api/v1.0/users/<string:user_id>', methods=['PUT'])
@auth.login_required
def update_user(user_id):
    """
    Update user specified with user ID and return updated user contents
    Note: Always return the appropriate response for the action requested.
    """
    schema = UserSchema()
    req = request.form or request.get_json()
    response = dict(errors=dict(), results=dict(), updated=False)

    data = schema.load(req)
    users = mongo_mgr.db.users
    update = users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': data.data},
    )

    if update.matched_count and update.modified_count:
        response['updated'] = True
        updated_user = users.find_one({'_id': ObjectId(user_id)})
        results = schema.dump(updated_user)
        response['results'] = results.data

    return jsonify(response)


@app.route('/prt/api/v1.0/users/<string:user_id>', methods=['DELETE'])
@auth.login_required
def delete_user(user_id):
    """
    Delete user specified in user ID
    Note: Always return the appropriate response for the action requested.
    """
    response = dict(errors=dict(), updated=False)

    users = mongo_mgr.db.users
    delete = users.delete_one(
        {'_id': ObjectId(user_id)},
    )

    response['updated'] = bool(delete.deleted_count)

    return jsonify(response)


@app.route('/prt/api/v1.0/distances', methods=['GET'])
@auth.login_required
def get_distances():
    """
    Each user has a lat/lon associated with them.  Determine the distance
    between each user pair, and provide the min/max/average/std as a json response.
    This should be GET only.
    You can use numpy or whatever suits you
    """
    response = dict(errors=dict(),
                    results=dict(min=0, max=0, avg=0, std=0), )

    db = mongo_mgr.db.users
    users = db.find()

    user_schema = UserSchema()
    results = user_schema.dump(users, many=True)
    coordinates = []

    for item in results.data:
        if 'coordinates' in item.get('location', dict()):
            coordinates.append(tuple(item['location']['coordinates']))

    response['results'] = calculate_distances(coordinates)

    return jsonify(response)


@app.route('/')
def index():
    if 'username' in session:
        return 'You are logged in as ' + session['username']

    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    schema = UserSchema()
    req = request.form or request.get_json()
    response = dict(errors=dict(), logged_in=False, results=dict())

    # Valid data or return errors
    try:
        data = schema.load(req).data
    except ValidationError as err:
        response['errors'] = err.messages

        return jsonify(response)

    users = mongo_mgr.db.users
    login_user = users.find_one({'username': data['username']})

    if login_user:
        if check_password_hash(login_user['password'],
                               data['password'].encode('utf-8')):
            session['username'] = data['username']

            response['results'] = schema.dump(login_user)
            response['logged_in'] = True

    return json.dumps(response)


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        req = request.form or request.get_json()
        register_user = new_user(req)

        if app.testing:
            return json.dumps(register_user)

        else:
            if not len(register_user['errors']):
                return redirect(url_for('index'))
            else:
                return register_user['errors'].get('user_exists')

    return render_template('register.html')


def new_user(req):
    schema = UserSchema()
    response = dict(errors=dict(), logged_in=False, results=dict())

    # Valid data or return errors
    try:
        data = schema.load(req).data
    except ValidationError as err:
        response['errors'] = err.messages

        return jsonify(response)

    users = mongo_mgr.db.users
    existing_user = users.find_one({'username': data['username']})

    if existing_user is None:
        hash_pass = generate_password_hash(data['password'])
        user = dict(
            username=data['username'],
            password=hash_pass,
            first_name=None,
            last_name=None,
            coordinates=dict(
                lat=None,
                lng=None,
            ),
        )

        add_user = users.insert_one(user)
        session['username'] = data['username']

        response['logged_in'] = True
        response['results']['username'] = session['username']
        response['results']['id'] = str(add_user.inserted_id)

        return response

    # User exists
    response['errors']['user_exists'] = 'This account already exists.'
    response['results'] = schema.dump(existing_user)

    return response


def calculate_distances(data):
    combis = set(itertools.combinations(data, 2))
    comb_list = [list(i[0] + i[1]) for i in combis]

    df_coords = pd.DataFrame(
        comb_list,
        columns=[
            'origin_lat',
            'origin_lng',
            'destination_lat',
            'destination_lng',
        ],
    )

    distances = haversine(df_coords.origin_lat, df_coords.origin_lng,
                          df_coords.destination_lat, df_coords.destination_lng)

    response = dict(
        min=numpy.min(distances),
        max=numpy.max(distances),
        avg=numpy.average(distances),
        std=numpy.std(distances),
    )

    return response


def haversine(a_lat, a_lng, b_lat, b_lng):
    """
    Haversine formula for calculating distances between coordinates, vectorized
    """
    R = 6371  # earth radius in km

    a_lat = numpy.radians(a_lat)
    a_lng = numpy.radians(a_lng)
    b_lat = numpy.radians(b_lat)
    b_lng = numpy.radians(b_lng)

    d_lat = b_lat - a_lat
    d_lng = b_lng - a_lng

    d_lat_sq = numpy.sin(d_lat / 2) ** 2
    d_lng_sq = numpy.sin(d_lng / 2) ** 2

    a = d_lat_sq + numpy.cos(a_lat) * numpy.cos(b_lat) * d_lng_sq
    c = 2 * numpy.arctan2(numpy.sqrt(a), numpy.sqrt(1 - a))

    return R * c  # returns distance between a and b in km


if __name__ == '__main__':
    app.run(debug=True)
