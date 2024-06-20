import functools
import random


from flask import Blueprint, flash, g, redirect, jsonify
from flask import render_template, request, session, url_for

from werkzeug.security import check_password_hash, generate_password_hash

from resumechat.db import get_db

random.seed()

bp = Blueprint('auth', __name__, url_prefix='/auth')

def createLink():
    alphabet = '1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    link = ''
    for i in range(6):
        nextchar = alphabet[random.randint(0, 62)]
        link += nextchar
    return link

def addUser(f_name, e_address, u_name, pword):
    link = createLink()
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO USER (name, email, username, password, link_id, subscr_status) VALUES (?, ?, ?, ?, ?, ?,)', (f_name, e_address, u_name, generate_password_hash(pword), link, 1), )
    db.commit()
    return cursor.lastrowid

def removeUser(u_name):
    db = get_db()
    error = ''
    try:
        db.execute('DELETE FROM USER WHERE username = ?', (u_name,))
        db.commit()
        return 'Success'
    except Error as e:
        error = str(e)
        return error

@bp.route('/register', methods=('GET', 'POST'))
def register():
    print(f'Session contents: {session}')
    for key, value in session.items():
        print(f'{key}: {value}')

    if request.method == 'POST':
        name = request.form['fullName']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required'
        elif not password:
            error = 'Password is required'
        elif not email:
            error = 'Email is required'
        elif not name:
            error = 'Full name is required'

        if error is None:
            # Need to create unique link, insert into DB, then set g.link to whatever it is
            link = createLink()
            try:
                user = db.execute('SELECT * FROM USER WHERE email = ?', (email,)).fetchone()
                db.execute('''
                           UPDATE USER SET name = ?, email = ?, username = ?, 
                           password = ?, link_id = ?
                           WHERE id = ?
                ''',
                (name, email, username, generate_password_hash(password), link, user['id']
                ))
                db.commit()                            

            except db.IntegrityError:
                error = f'User {username} is already registered.'
            else:
                return redirect(url_for('auth.login'))

        flash(error)
    db = get_db()
    try:
        user = db.execute('SELECT * FROM USER WHERE id = ?', (session['user_id'],)).fetchone()
        return render_template('auth/register.html', fullName=user['name'], emailAddress=user['email'])
    except KeyError:
        return render_template('auth/register.html', fullName='', emailAdress='')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute('SELECT * FROM USER WHERE username = ?', (username,)).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password'

        if error is None:
            if user['subscr_status'] == 1:
                session.clear()
                session['user_id'] = user['id']
                session['link_id'] = user['link_id']
                # load_logged_in_user()
                return redirect(url_for('application.editInfo'))  # application.editInfo() is defined in application.py

            else:
                error = 'Your account has expired'

        flash(error)

    return render_template('auth/login.html')

@bp.route('/account', methods=('GET', 'POST'))
def account():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute('SELECT * FROM USER WHERE id = ?', (g.user,)).fetchone()

        if user is None:
            error = 'User does not exist'
        else:

            if password != '':
                hashed_password = generate_password_hash(password)
                try:
                    db.execute('''
                               UPDATE USER SET email = ?, username = ?, password = ? WHERE id = ?
                               ''',
                               (email, username, hashed_password, session['user_id']
                               ))
                    db.commit()
                    return redirect(url_for('application.editInfo'))
                except:
                    error = 'Unknown error'
            else:
                try:
                    db.execute('''
                               UPDATE USER SET email = ?, username = ? WHERE id = ?
                               ''',
                               (email, username, session['user_id']
                               ))
                    db.commit()
                    return redirect(url_for('application.editInfo'))
                except:
                    error = 'Unknown error'

    db = get_db()
    user = db.execute('SELECT * FROM USER WHERE id = ?', (session['user_id'],)).fetchone()
    return render_template('auth/account.html', emailAddress=user['email'], username=user['username'])

@bp.route('/siteadmin', methods=['GET', 'POST'])
def siteadmin():
    if session['user_id'] != 2:
        return redirect(url_for('application.index'))
    
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'add_user':
            result = addUser(request.form.get('fullName'),
                             request.form.get('email'),
                             request.form.get('addUsername'),
                             request.form.get('password'))
            return jsonify(result)
        elif form_type == 'remove_user':
            result = removeUser(request.form.get('remUsername'))
            return jsonify(result)
    return render_template('auth/siteadmin.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    link_id = session.get('link_id')

    if user_id is None:
        g.user = None
        g.link = None
    else:
        g.user = get_db().execute('SELECT * FROM USER WHERE id = ?', (user_id,)).fetchone()
        g.link = link_id


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
    
