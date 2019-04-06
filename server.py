#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os
import traceback
import flask_login
import datetime
from sqlalchemy import *
from flask import Flask, request, render_template, g, redirect, Response, session, url_for, flash

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = b"\x19~'\xe6SH\xece\xe7\xe4\xa8\xe2\x9d\x17\xef\xbd"

DATABASEURL = "postgresql://cd3032:2203@34.73.21.127/proj1part2"
engine = create_engine(DATABASEURL)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


def time_now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def str2datetime(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

def double_quote(s):
    return "'" + s + "'"


# flask_login.current_user
class User(flask_login.UserMixin):
    def __init__(self, user_id, name, isAdmin=False):
        self.id = user_id
        self.name = name
        self.isAdmin = isAdmin

    def get_id(self):
        return str(self.id) + ' ' + str(self.isAdmin)


@login_manager.user_loader
def user_loader(user_id):
    """
    :param user_id: str of 'id isAdmin'
    :return:
    """
    user_id, isAdmin = user_id.split(' ')
    user_id, isAdmin = int(user_id), bool(isAdmin)

    if not isAdmin:
        cursor = g.conn.execute("SELECT * FROM users WHERE user_id={};".format(user_id))
        row = cursor.fetchone()
        if row:
            user = User(row['user_id'], row['name'], False)
        else:
            user = None
        cursor.close()
        return user
    else:
        cursor = g.conn.execute("SELECT * FROM admin WHERE admin_id={};".format(user_id))
        row = cursor.fetchone()
        if row:
            user = User(row['admin_id'], row['name'], True)
        else:
            user = None
        cursor.close()
        return user



@app.before_request
def before_request():
    """
    This function is run at the beginning of every web request
    (every time you enter an address in the web browser).
    We use it to setup a database connection that can be used throughout the request.

    The variable g is globally accessible.
    """
    try:
        g.conn = engine.connect()
    except:
        print("uh oh, there is a problem in connecting to database")
        traceback.print_exc()
        g.conn = None


@app.teardown_request
def teardown_request(exception):
    """
    At the end of the web request, this makes sure to close the database connection.
    If you don't, the database could run out of memory!
    """
    print(exception)
    try:
        g.conn.close()
    except Exception as e:
        print(e)


# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
@app.route('/')
def index():
    """
    request is a special object that Flask provides to access web request information:

    request.method:   "GET" or "POST"
    request.form:     if the browser submitted a form, this contains the data in the form
    request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

    See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
    """

    # DEBUG: this is debugging code to see what request looks like
    print(request.args)

    #
    # Flask uses Jinja templates, which is an extension to HTML where you can
    # pass data to a template and dynamically generate HTML based on the data
    # (you can think of it as simple PHP)
    # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
    #
    # You can see an example template in templates/index.html
    #
    # context are the variables that are passed to the template.
    # for example, "data" key in the context variable defined below will be
    # accessible as a variable in index.html:
    #
    #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
    #     <div>{{data}}</div>
    #
    #     # creates a <div> tag for each element in data
    #     # will print:
    #     #
    #     #   <div>grace hopper</div>
    #     #   <div>alan turing</div>
    #     #   <div>ada lovelace</div>
    #     #
    #     {% for n in data %}
    #     <div>{{n}}</div>
    #     {% endfor %}
    #

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("index.html")


@app.route('/world', methods=['GET'])
def world():
    cursor = g.conn.execute("SELECT C.c_id, C.image, C.text, COUNT(L.user_id) as likes \n"
                            "FROM content as C LEFT JOIN like_relation as L ON C.c_id=L.content_id \n"
                            "GROUP BY C.c_id, C.image, C.text \n"
                            "ORDER BY C.c_id;")
    content = {}
    for result in cursor:
        content[result['c_id']] = [result['image'], result['text'], result['likes']]
    cursor.close()

    context = dict(data=content)
    return render_template('world.html', **context)


def get_categories(user_id):
    scmd_01 = "SELECT C.c_id as c_id, C.interest_area as interest_area \n" \
              "FROM category as C, users as U, belongto_relation as B \n" \
              "WHERE U.user_id=B.user_id AND C.c_id=B.c_id AND U.user_id={};".format(user_id)
    cursor = g.conn.execute(scmd_01)
    category = []
    for result in cursor:
        dic = dict()
        dic['c_id'] = result['c_id']
        dic['interest_area'] = result['interest_area']
        category.append(dic)
    cursor.close()
    return category

@app.route('/show/<c_id>', methods=['GET'])
def show(c_id):
    # why use RIGHT JOIN? Think about this: c_id is not in like_relation
    scmd_0 = "SELECT C.c_id as c_id, U.user_id as user_id, U.name as name, " \
             "C.image as image, C.text as text, \n" \
             "(SELECT COUNT(L.user_id) " \
             "FROM like_relation as L RIGHT JOIN content as C1 ON C1.c_id=L.content_id " \
             "WHERE C1.c_id=C.c_id) as likes \n" \
             "FROM content as C, users as U, postcontent_relation as P " \
             "WHERE C.c_id={} AND U.user_id=P.user_id AND P.content_id=C.c_id;".format(c_id, c_id)

    cursor = g.conn.execute(scmd_0)
    row = cursor.fetchone()

    content = dict()
    if not row:
        raise SystemError('Error in searching for content-{}'.format(c_id))
    content['content_id'] = row['c_id']
    content['image'] = row['image']
    content['text'] = row['text']
    content['user_id'] = row['user_id']
    content['name'] = row['name']
    content['likes'] = row['likes']
    cursor.close()

    cursor = g.conn.execute('SELECT * FROM follow_relation F WHERE F.follower_id=%s AND F.following_id=%s;',
                            (flask_login.current_user.id, content['user_id']))
    row = cursor.fetchone()
    if row or content['user_id'] == flask_login.current_user.id:
        content['has_followed'] = True
    else:
        content['has_followed'] = False
    cursor.close()
    scmd_1 = "SELECT R.time as time, C.text as text, U.name as name, U.user_id as user_id \n" \
             "FROM comments as C, commentat_relation as R, postcomment_relation as P, users as U \n" \
             "WHERE C.c_id=R.comment_id AND R.content_id={} AND U.user_id=P.user_id \n" \
             "AND P.comment_id=C.c_id;".format(c_id)
    cursor = g.conn.execute(scmd_1)
    comments = []
    for result in cursor:
        d = dict()
        d['user_id'] = result['user_id']
        d['name'] = result['name']
        d['text'] = result['text']
        d['time'] = result['time']
        comments.append(d)

    context = dict(data=content)
    context['comments'] = comments
    context['category'] = get_categories(content['user_id'])
    cursor.close()
    return render_template('show.html', **context)

@app.route('/profile', methods=['GET'])
def profile():
    sql_cmd = "SELECT C.c_id as c_id, " \
              "(SELECT COUNT(L.user_id) FROM like_relation as L RIGHT JOIN content as C1 ON L.content_id=C1.c_id\n" \
              "WHERE C1.c_id=C.c_id) as likes, " \
              "C.image as image, C.text as text\n" \
              "FROM postcontent_relation as P, content as C\n" \
              "WHERE P.content_id = C.c_id AND P.user_id={};".format(flask_login.current_user.id)
    cursor = g.conn.execute(sql_cmd)
    contents = []
    for result in cursor:
        content = dict()
        content['content_id'] = result['c_id']
        content['likes'] = result['likes']
        content['image'] = result['image']
        content['text'] = result['text']
        contents.append(content)
    cursor.close()
    context = dict(data=contents)

    scmd_01 = "SELECT C.c_id as c_id, C.interest_area as interest_area \n" \
              "FROM category as C, users as U, belongto_relation as B \n" \
              "WHERE U.user_id=B.user_id AND C.c_id=B.c_id AND U.user_id={};".format(flask_login.current_user.id)
    cursor = g.conn.execute(scmd_01)
    category = []
    for result in cursor:
        dic = dict()
        dic['c_id'] = result['c_id']
        dic['interest_area'] = result['interest_area']
        category.append(dic)
    cursor.close()
    context['category'] = category
    return render_template('profile.html', **context)


@app.route('/following', methods=['GET'])
def following():
    sql_cmd = "SELECT C.c_id as content_id, " \
              "(SELECT COUNT(L.user_id) FROM like_relation as L RIGHT JOIN content as C1 ON C1.c_id=L.content_id\n" \
              "WHERE C1.c_id=C.c_id) as likes, " \
              "C.image as image, C.text as text, P.user_id as user_id, U.name as name \n" \
              "FROM follow_relation as F, content as C, postcontent_relation as P, users as U \n" \
              "WHERE F.follower_id={} AND P.content_id=C.c_id AND P.user_id=F.following_id " \
              "AND U.user_id=F.following_id;".format(flask_login.current_user.id)

    cursor = g.conn.execute(sql_cmd)
    fs = dict()
    for result in cursor:
        following_id = result['user_id']
        if following_id not in fs:
            fs[following_id] = []
        content = dict()
        content['name'] = result['name']
        content['c_id'] = result['content_id']
        content['likes'] = result['likes']
        content['image'] = result['image']
        content['text'] = result['text']
        content['category'] = get_categories(following_id)
        fs[following_id].append(content)
    cursor.close()
    context = dict(data=fs)

    return render_template('following.html', **context)

'''
TODO administor delete an event
'''
def admin_del_event(e_id):
    """
    only allow administrator to delete an event published by him/her
    enforced by: e_id

    :param e_id:
    :return:
    """
    scmd_1 = "DELETE FROM event WHERE e_id={};".format(e_id)
    g.conn.execute(scmd_1)

"""
TODO
Ideas of using GROUP BY
1. calculate the number of events by address
2. TODO
3. TODO
"""


'''
TODO administrator login page
see all published events
'''
def event_by_admin(admin_id):
    scmd_1 = "SELECT E.e_id as e_id, A.addr_id as addr_id, " \
             "A.city as city, A.street as street, A.zipcode as zipcode," \
             "E.start_time as start_time, E.end_time = E.end_time\n" \
             "FROM event as E, at_relation as R, address as A, admin as D\n" \
             "WHERE E.e_id=R.e_id AND A.addr_id=R.addr_id AND D.admin_id={};".format(admin_id)
    cursor = g.conn.execute(scmd_1)
    events = []
    for result in cursor:
        content = dict()
        content['e_id'] = result['e_id']
        content['addr_id'] = result['addr_id']
        content['city'] = result['city']
        content['street'] = result['streeet']
        content['zipcode'] = result['zipcode']
        content['start_time'] = result['start_time']
        content['end_time'] = result['end_time']
        events.append(content)
    cursor.close()

"""
get all events registered by user
"""
def event_by_user(user_id):
    scmd_1 = "SELECT E.e_id as e_id, A.addr_id as addr_id, G.time as time, " \
             "A.city as city, A.street as street, A.zipcode as zipcode," \
             "E.start_time as start_time, E.end_time = E.end_time\n" \
             "FROM event as E, at_relation as R, address as A, users as U, register_relation as G\n" \
             "WHERE E.e_id=R.e_id AND A.addr_id=R.addr_id AND U.user_id={} " \
             "AND G.user_id=U.user_id AND G.event_id=E.e_id;".format(user_id)
    cursor = g.conn.execute(scmd_1)
    events = []
    for result in cursor:
        content = dict()
        content['e_id'] = result['e_id']
        content['addr_id'] = result['addr_id']
        content['city'] = result['city']
        content['street'] = result['streeet']
        content['zipcode'] = result['zipcode']
        content['start_time'] = result['start_time']
        content['end_time'] = result['end_time']
        content['register_time'] = result['time']
        events.append(content)
    cursor.close()


def register_event(e_id, user_id):
    """
    fecthes start_time and end_time from event table first
    check if now() < event.end_time
    :param e_id:
    :param user_id:
    :return: True if successfully registered, False if not successful
    """
    # now = datetime.datetime.now()
    # end_time = str2datetime(end_time)
    # if now >= end_time:
    #     return False


    scmd_1 = "INSERT INTO register_relation(user_id, event_id) " \
             "VALUES ({}, {});".format(user_id, e_id)
    g.conn.execute(scmd_1)
    return True

@app.route('/event', methods=['GET'])
def event():
    """
    get all events
    """
    scmd_1 = "SELECT E.e_id as e_id, A.addr_id as addr_id, " \
             "A.city as city, A.street as street, A.zipcode as zipcode," \
             "E.start_time as start_time, E.end_time as end_time\n" \
             "FROM event as E, at_relation as R, address as A\n" \
             "WHERE E.e_id=R.e_id AND A.addr_id=R.addr_id;"
    cursor = g.conn.execute(scmd_1)
    events = []
    for result in cursor:
        # filter out events whose end_time < now
        if result['end_time'] < datetime.datetime.now():
            continue
        content = dict()
        content['e_id'] = result['e_id']
        content['addr_id'] = result['addr_id']
        content['city'] = result['city']
        content['street'] = result['street']
        content['zipcode'] = result['zipcode']
        content['start_time'] = result['start_time']
        content['end_time'] = result['end_time']

        cursor_1 = g.conn.execute('SELECT * FROM register_relation R WHERE R.user_id=%s AND R.event_id=%s;',
                                (flask_login.current_user.id, content['e_id']))
        row = cursor_1.fetchone()
        if row:
            content['has_registered'] = True
        else:
            content['has_registered'] = False
        cursor_1.close()
        events.append(content)
    cursor.close()
    context = dict(data=events)
    return render_template('event.html', **context)

@app.route('/event_user/<e_id>', methods=['GET'])
def event_user(e_id):
    scmd_1 = "SELECT U.name as name, U.user_id as user_id FROM register_relation R, users U "\
             "WHERE R.user_id=U.user_id AND R.event_id={};".format(e_id)
    cursor = g.conn.execute(scmd_1)
    users = []
    for result in cursor:
        user = dict()
        user['user_id'] = result['user_id']
        user['name'] = result['name']
        users.append(user)
    cursor.close()
    context = dict(data=users)
    return render_template('event-user.html', **context)

@app.route('/registerEvent', methods=['POST'])
def registerEvent():
    register_event(request.form.get('event_id'), flask_login.current_user.id)
    return redirect(url_for('event'))



@app.route('/addComment', methods=['POST'])
def addComment():
    text = request.form.get('text')
    content_id = request.form.get('content_id')

    scmd_1 = "INSERT INTO comments(text) VALUES (%s) RETURNING c_id;"
    cursor = g.conn.execute(scmd_1, text)
    row = cursor.fetchone()
    if not row:
        raise SystemError('Error in inserting into comments table')
    cursor.close()

    c_id = row['c_id']
    scmd_1_del = "DELETE FROM comments WHERE c_id={};".format(c_id)
    scmd_2 = "INSERT INTO postcomment_relation(user_id, comment_id) " \
             "VALUES ({}, {});".format(flask_login.current_user.id, c_id)
    try:
        g.conn.execute(scmd_2)
    except Exception as ex:
        g.conn.execute(scmd_1_del)
        raise ex


    scmd_2_del = "DELETE FROM postcomment_relation " \
                 "WHERE user_id={}, comment_id={};".format(flask_login.current_user.id, c_id)
    scmd_3 = "INSERT INTO commentat_relation(comment_id, content_id, time)" \
             "VALUES ({}, {}, {});".format(c_id, content_id, double_quote(time_now()))
    try:
        g.conn.execute(scmd_3)
    except Exception as ex:
        g.conn.execute(scmd_1_del)
        g.conn.execute(scmd_2_del)
        raise ex

    return redirect(url_for('show', c_id = content_id))


@app.route('/addContent', methods=['POST'])
def addContent():
    image = request.form.get('image')
    image = double_quote(image)
    text = double_quote(request.form.get('text'))
    scmd_1 = "INSERT INTO content(image, text) " \
             "VALUES ({}, {}) RETURNING c_id;".format(image, text)
    cursor = g.conn.execute(scmd_1)
    row = cursor.fetchone()
    if not row: raise SystemError('Error in inserting into content table')
    c_id = row['c_id']
    cursor.close()
    scmd_1_del = "DELETE FROM content WHERE c_id={}".format(c_id)
    scmd_2 = "INSERT INTO postcontent_relation(content_id, user_id, time) " \
             "VALUES ({}, {}, {});".format(c_id, flask_login.current_user.id, double_quote(time_now()))

    try:
        g.conn.execute(scmd_2)
    except Exception as ex:
        g.conn.execute(scmd_1_del)
        raise  ex

    return redirect(url_for('profile'))



@app.route('/addFollowing', methods=['POST'])
def addFollowing():
    following_id = request.form.get('user_id')
    scmd_1 = "INSERT INTO follow_relation(following_id, follower_id) " \
             "VALUES ({}, {});".format(following_id, flask_login.current_user.id)
    g.conn.execute(scmd_1)
    return redirect(url_for('following'))



@app.route('/deleteContent', methods=['POST'])
def deleteContent():
    content_id = request.form.get('content_id')
    '''
    If only delete entries in content table, entries in comments table won't be deleted
    '''
    scmd_02 = "DELETE FROM comments \n" \
              "WHERE c_id in (SELECT C.c_id \n" \
                             "FROM comments as C, commentat_relation as P \n" \
                              "WHERE C.c_id=P.comment_id AND P.content_id={});".format(content_id)

    scmd_01 = "DELETE FROM content WHERE c_id={};".format(content_id)
    g.conn.execute(scmd_02)
    g.conn.execute(scmd_01)
    return redirect(url_for('profile'))



@app.route('/deleteFollowing', methods=['POST'])
def deleteFollowing():
    following_id = request.form.get('user_id')
    scmd_01 = "DELETE FROM follow_relation " \
              "WHERE follower_id={} and following_id={};".format(flask_login.current_user.id, following_id)
    g.conn.execute(scmd_01)
    return redirect(url_for('following'))



@app.route('/modifyCategory', methods=['POST'])
def modifyCategory():
    temp_dict = request.form.lists()
    selectedCategory = temp_dict[0][1]

    user_id = flask_login.current_user.id
    scmd_01 = "DELETE FROM belongto_relation " \
              "WHERE user_id={};".format(user_id)
    g.conn.execute(scmd_01)

    values = ['({}, {})'.format(user_id, c_id) for c_id in selectedCategory]
    scmd_02 = "INSERT INTO belongto_relation(user_id, c_id) " \
              "VALUES {};".format(', '.join(values))
    g.conn.execute(scmd_02)
    return redirect(url_for('profile'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        dateOfBirth = request.form['dateOfBirth']
        try:

            cursor = g.conn.execute("SELECT * FROM users WHERE name=%s;", username)
            row = cursor.fetchone()
            if row:
                error = 'duplicate name detected, use a different name'
                return render_template('register.html', error=error)


            # use this to get auto-incremented primary key value
            cursor = g.conn.execute("INSERT INTO users(date_of_birth, pwd, name) \n"
                                    "VALUES (%s, %s, %s) RETURNING user_id;", (dateOfBirth, password, username))
            row = cursor.fetchone()
            if not row: raise SystemError('Insertion failed')
            print('Created user with id {}'.format(row['user_id']))
            return redirect(url_for('login'))

        except Exception as e:
            print(e)
            error = 'error occured in executing SQL command'
            return render_template('register.html', error=error)

    else:
        return render_template('register.html')


# TODO write a html for administrator login
def login_admin():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        cursor = g.conn.execute("SELECT * FROM admin WHERE name=%s AND pwd=%s;", (username, password))

        row = cursor.fetchone()
        cursor.close()
        if row:
            user = User(row['admin_id'], row['name'], True)
            print(row['admin_id'], row['name'], row['pwd'], 'Admin')
            flask_login.login_user(user)
            print("Successfully login")

            # TODO change redirection to admin's page
            return redirect(url_for("world"))

        else:
            error = 'Invalid username or password. Please try again!'
            flash(error)

            # TODO redirect to admin's login html
            return render_template('login.html')

    else:
        return render_template("login.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        cursor = g.conn.execute("SELECT * FROM users WHERE name=%s AND pwd=%s;", (username, password))

        row = cursor.fetchone()
        cursor.close()
        if row:
            user = User(row['user_id'], row['name'], False)
            print(row['user_id'], row['name'], row['pwd'], 'Not Admin')
            flask_login.login_user(user)
            print("Successfully login")
            return redirect(url_for("world"))

        else:
            error = 'Invalid username or password. Please try again!'
            flash(error)
            return render_template('login.html')

    else:
        return render_template("login.html")




@app.route('/logout', methods=['GET'])
@flask_login.login_required
def logout():
    flask_login.logout_user()

    return redirect(url_for('index'))




if __name__ == "__main__":
    import click
    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):

        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)
    run()
