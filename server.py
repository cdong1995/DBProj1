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


# flask_login.current_user
class User(flask_login.UserMixin):
    def __init__(self, user_id, name):
        self.id = user_id
        self.name = name

    def get_id(self):
        return self.id


@login_manager.user_loader
def user_loader(user_id):
    cursor = g.conn.execute("SELECT * FROM users WHERE user_id={}".format(user_id))
    row = cursor.fetchone()
    if row:
        return User(row['user_id'], row['name'])
    else:
        return None


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
        print("uh oh, problem connecting to database")
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
    cursor = g.conn.execute("SELECT c_id, image, text, likes FROM content")
    content = {}
    for result in cursor:
        content[result['c_id']] = [result['image'], result['text'], result['likes']]
    cursor.close()

    context = dict(data=content)
    # print(context)
    return render_template('world.html', **context)


'''
2. 显示content的作者

'''
@app.route('/show/<c_id>', methods=['GET'])
def show(c_id):
    cursor = g.conn.execute("SELECT * FROM content WHERE c_id = %s", c_id)
    row = cursor.fetchone()
    content = dict()
    # if not row: raise SystemError('Error in inserting into comments table')
    content['content_id'] = row['c_id']
    content['image'] = row['image']
    content['text'] = row['text']
    content['likes'] = row['likes']
    cursor.close()

    scmd_1 = "SELECT R.time as time, C.text as text \n, U.name as name, U.user_id as user_id \n" \
             "FROM comments as C, commentat_relation as R, postcomment_relation as P, users as U \n" \
             "WHERE C.c_id=R.comment_id AND R.content_id={} AND U.user_id=P.user_id \n" \
             "AND P.comment_id=C.c_id".format(c_id)
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
    # TODO content not including comments
    return render_template('show.html', **context)


'''
escape error!!! If add comment, "It's a comment" => error 
'''
@app.route('/addComment', methods=['POST'])
def addComment():
    # you need to get text and content_id
    text = request.form.get('text')
    text = "'" + text + "'"
    content_id = request.form.get('content_id')
    scmd_1 = "INSERT INTO comments(text) VALUES ({}) RETURNING c_id".format(text)
    cursor = g.conn.execute(scmd_1)
    row = cursor.fetchone()
    if not row: raise SystemError('Error in inserting into comments table')
    c_id = row['c_id']

    scmd_2 = "INSERT INTO postcomment_relation(user_id, comment_id) " \
             "VALUES ({}, {})".format(flask_login.current_user.id, c_id)
    g.conn.execute(scmd_2)

    scmd_3 = "INSERT INTO commentat_relation(comment_id, content_id, time)" \
             "VALUES ({}, {}, {})".format(c_id, content_id, "'" + time_now() + "'")
    g.conn.execute(scmd_3)
    return redirect(url_for('show', c_id = content_id))



@app.route('/addContent', methods=['POST'])
def addContent():
    image = request.form.get('image')
    image = str(image).encode('string-escape')
    image = "'" + image + "'"
    print('WARNING*******', image)
    text = request.form.get('text')
    text = "'" + text + "'"
    scmd_1 = "INSERT INTO content(image, text) " \
             "VALUES ({}, {}) RETURNING c_id".format(image, text)
    cursor = g.conn.execute(scmd_1)
    row = cursor.fetchone()
    if not row: raise SystemError('Error in inserting into content table')
    c_id = row['c_id']

    scmd_2 = "INSERT INTO postcontent_relation(content_id, user_id, time) " \
             "VALUES ({}, {}, {})".format(c_id, flask_login.current_user.id, "'" + time_now() + "'")

    g.conn.execute(scmd_2)
    return redirect(url_for('profile'))

@app.route('/addFollowing', methods=['POST'])
def addFollowing():
    following_id = None
    scmd_1 = "INSERT INTO follow_relation(following_id, follower_id) " \
             "VALUES ({}, {})".format(following_id, flask_login.current_user.id)
    g.conn.execute(scmd_1)


@app.route('/deleteContent', methods=['POST'])
def deleteContent():
    content_id = request.form.get('content_id')
    print(content_id)
    # TODO

    return redirect(url_for('profile'))

@app.route('/deleteFollowing', methods=['POST'])
def deleteFollowing():
    # TODO
    pass

'''
3. 修改当前用户的category
'''
@app.route('/profile', methods=['GET'])
def profile():
    sql_cmd = "SELECT C.c_id as c_id, C.likes as likes, C.image as image, C.text as text\n" \
              "FROM postcontent_relation as P, content as C\n" \
              "WHERE P.content_id = C.c_id AND P.user_id={}".format(flask_login.current_user.id)
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
    print(contents)
    context = dict(data=contents)
    return render_template('profile.html', **context)


'''
1. 显示当前用户的following，及每个following的<=4个content
'''
@app.route('/following', methods=['GET'])
def following():
    sql_cmd = "SELECT C.c_id as content_id, C.likes as likes, C.image as image, C.text as text, P.user_id as user_id, U.name as name \n" \
              "FROM follow_relation as F, content as C, postcontent_relation as P, users as U \n" \
              "WHERE F.follower_id={} AND P.content_id=C.c_id AND P.user_id=F.following_id " \
              "AND U.user_id=F.following_id".format(flask_login.current_user.id)

    print(sql_cmd)
    cursor = g.conn.execute(sql_cmd)
    fs = dict()
    for result in cursor:
        following_id = result['user_id']
        if following_id not in fs:
            fs[following_id] = []
        content = dict()

        # duplicates
        content['name'] = result['name']

        content['c_id'] = result['content_id']
        content['likes'] = result['likes']
        content['image'] = result['image']
        content['text'] = result['text']
        fs[following_id].append(content)
    print(fs)
    context = dict(data=fs)
    return render_template('following.html', **context)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        dateOfBirth = request.form['dateOfBirth']
        print(dateOfBirth)
        try:
            # use this to get auto-incremented primary key value
            cursor = g.conn.execute("INSERT INTO users(date_of_birth, pwd, name) \n"
                                    "VALUES (%s, %s, %s) RETURNING user_id", (dateOfBirth, password, username))
            row = cursor.fetchone()
            if not row: raise SystemError('Insertion failed')
            print('Created user with id {}'.format(row['user_id']))
            return redirect(url_for('world'))

        except Exception as e:
            print(e)
            error = 'error occured in executing SQL command'
            return render_template('register.html', error=error)

    else:
        return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        cursor = g.conn.execute("SELECT * FROM users WHERE name=%s AND pwd=%s", (username, password))

        row = cursor.fetchone()
        if row:
            user = User(row['user_id'], row['name'])
            print(row['user_id'], row['name'], row['pwd'])

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
