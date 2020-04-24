from flask import Flask, render_template, request, redirect, url_for, session
from google.cloud import datastore

# from google.appengine.ext import ndb
import re

datastore_client = datastore.Client()
app = Flask(__name__)

app.config['SESSION_PERMANENT'] = False
app.config['USE_SESSION_FOR_NEXT'] = False
app.config['SECRET_KEY'] = b'\xf8\xde\xce\xaa \xb5"\xa9\x9eA\xaa\x9d\xa4\xbf\x8d*'


def valid_credentials(user_password, password):
    return user_password == password


@app.route('/')
def to_login():
    return redirect(url_for('login_user'))


@app.route('/login', methods=['GET', 'POST'])
def login_user():
    # clear session
    session.pop('id', None)

    if request.method == 'POST':
        user_id = request.form.get('id')
        password = request.form.get('password')

        if (len(str(user_id)) > 0 and len(str(password)) > 0):
            session['id'] = user_id
            user = datastore_client.get(
                datastore_client.key('user', session['id']))

            if user is not None:
                if valid_credentials(user['password'], int(password)):
                    return redirect(url_for('main'))

        # display error message
        return render_template('login.html', valid=False)

    return render_template('login.html', valid=True)


@app.route('/main', methods=['GET', 'POST'])
def main():
    return render_template('main.html', user=datastore_client.get(
        datastore_client.key('user', session['id'])))


@app.route('/name', methods=['POST'])
def change_name():
    user = datastore_client.get(datastore_client.key('user', session['id']))

    if str(request.form.get('first')) == 'False':
        newname = request.form.get('name')

        if (len(newname.strip())) > 0:
            with datastore_client.transaction():
                # copy all existing property values of the entity
                for prop in user:
                    user[prop] = user[prop]

                user['name'] = newname
                datastore_client.put(user)

            return redirect(url_for('main'))

        return render_template('name.html', valid=False, user=user)

    return render_template('name.html', valid=True, user=user)


@app.route('/password', methods=['POST'])
def change_password():
    user = datastore_client.get(datastore_client.key('user', session['id']))

    if str(request.form.get('first')) == 'False':
        oldpassword = request.form.get('oldpassword')
        newpassword = request.form.get('newpassword')

        # regex reference: N. Batchelder, Removing All Non-numeric Characters From String In Python. Available: https://stackoverflow.com/a/1249424
        old_stripped = re.sub("[^\d\.]", "", str(oldpassword))

        if len(str(old_stripped)) > 0 and valid_credentials(user['password'], int(old_stripped)):
            if len(str(re.sub("[^\d\.]", "", str(newpassword)))) == 0:
                return render_template('password.html', valid=True, empty=True)

            with datastore_client.transaction():
                for prop in user:
                    user[prop] = user[prop]

                user['password'] = int(re.sub("[^\d\.]", "", str(newpassword)))
                datastore_client.put(user)

            return redirect(url_for('login_user'))

        return render_template('password.html', valid=False, empty=False)

    return render_template('password.html', valid=True, empty=False)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
