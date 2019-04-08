#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os
import traceback
import flask_login
import datetime
from sqlalchemy import *
import psycopg2
from flask import Flask, request, render_template, g, redirect, Response, session, url_for, flash

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = b"\x19~'\xe6SH\xece\xe7\xe4\xa8\xe2\x9d\x17\xef\xbd"

DATABASEURL = "postgresql://cd3032:2203@34.73.21.127/proj1part2"
engine = create_engine(DATABASEURL)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

"""
add more events
add more likes
"""


def time_now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def str2datetime(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

def double_quote(s):
    return "'" + s + "'"

def check_user_type():
    return flask_login.current_user.get_id().split(' ')[1]


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
    user_id, isAdmin = int(user_id), isAdmin == 'True'

    if not isAdmin:
        try:
            cursor = g.conn.execute("SELECT * FROM users WHERE user_id={};".format(user_id))
        except (Exception, psycopg2.Error, SystemError) as ex:
            return render_error(str(ex))
        row = cursor.fetchone()
        if row:
            user = User(row['user_id'], row['name'], False)
        else:
            user = None
        cursor.close()
        return user
    else:
        try:
            cursor = g.conn.execute("SELECT * FROM admin WHERE admin_id={};".format(user_id))
        except (Exception, psycopg2.Error, SystemError) as ex:
            return render_error(str(ex))
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
        return render_error(str('Error in connecting to database'))


@app.teardown_request
def teardown_request(exception):
    """
    At the end of the web request, this makes sure to close the database connection.
    If you don't, the database could run out of memory!
    """
    #print(exception)
    try:
        g.conn.close()
    except Exception as e:
        return render_error(str(e))



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
    #print(request.args)

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


def render_error(msg):
    content = {'error':msg}
    return render_template('error.html', **content)


@app.route('/world', methods=['GET'])
def world():
    if check_user_type() == 'True':
        return redirect(url_for('admin_event'))
    try:
        cursor = g.conn.execute("SELECT C.c_id, C.image, C.text, COUNT(L.user_id) as likes \n"
                                "FROM content as C LEFT JOIN like_relation as L ON C.c_id=L.content_id \n"
                                "GROUP BY C.c_id, C.image, C.text \n"
                                "ORDER BY C.c_id ASC;")
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))
    content = {}
    for result in cursor:
        content[result['c_id']] = [result['image'], result['text'], result['likes']]
    cursor.close()

    context = dict(data=content)
    return render_template('world.html', **context)


def get_categories(user_id):
    try:
        scmd_01 = "SELECT C.c_id as c_id, C.interest_area as interest_area \n" \
                  "FROM category as C, users as U, belongto_relation as B \n" \
                  "WHERE U.user_id=B.user_id AND C.c_id=B.c_id AND U.user_id={} " \
                  "ORDER BY C.c_id ASC;".format(user_id)
        cursor = g.conn.execute(scmd_01)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))
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
    if check_user_type() == 'True':
        return redirect(url_for('admin_event'))
    # why use RIGHT JOIN? Think about this: c_id is not in like_relation
    scmd_0 = "SELECT C.c_id as c_id, U.user_id as user_id, U.name as name, " \
             "C.image as image, C.text as text, \n" \
             "(SELECT COUNT(L.user_id) " \
             "FROM like_relation as L RIGHT JOIN content as C1 ON C1.c_id=L.content_id " \
             "WHERE C1.c_id=C.c_id) as likes \n" \
             "FROM content as C, users as U, postcontent_relation as P " \
             "WHERE C.c_id={} AND U.user_id=P.user_id AND P.content_id=C.c_id " \
             "ORDER BY C.c_id DESC ;".format(c_id, c_id)

    try:
        cursor = g.conn.execute(scmd_0)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))

    row = cursor.fetchone()

    content = dict()
    if not row:
        return render_error('Error in searching for content-{}'.format(c_id))
    content['content_id'] = row['c_id']
    content['image'] = row['image']
    content['text'] = row['text']
    content['user_id'] = row['user_id']
    content['name'] = row['name']
    content['likes'] = row['likes']
    cursor.close()

    try:
        cursor = g.conn.execute('SELECT * FROM follow_relation F WHERE F.follower_id=%s AND F.following_id=%s;',
                                (flask_login.current_user.id, content['user_id']))
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))

    row = cursor.fetchone()
    if row or content['user_id'] == flask_login.current_user.id:
        content['has_followed'] = True
    else:
        content['has_followed'] = False
    cursor.close()
    try:
        cursor = g.conn.execute('SELECT * FROM like_relation L WHERE L.user_id=%s AND L.content_id=%s;',
                                (flask_login.current_user.id, content['content_id']))
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))

    row = cursor.fetchone()
    if row:
        content['has_liked'] = True
    else:
        content['has_liked'] = False
    cursor.close()
    scmd_1 = "SELECT R.time as time, C.text as text, U.name as name, U.user_id as user_id \n" \
             "FROM comments as C, commentat_relation as R, postcomment_relation as P, users as U \n" \
             "WHERE C.c_id=R.comment_id AND R.content_id={} AND U.user_id=P.user_id \n" \
             "AND P.comment_id=C.c_id;".format(c_id)
    try:
        cursor = g.conn.execute(scmd_1)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))
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
    if check_user_type() == 'True':
        return redirect(url_for('login'))
    sql_cmd = "SELECT C.c_id as c_id, " \
              "(SELECT COUNT(L.user_id) FROM like_relation as L RIGHT JOIN content as C1 ON L.content_id=C1.c_id\n" \
              "WHERE C1.c_id=C.c_id) as likes, " \
              "C.image as image, C.text as text\n" \
              "FROM postcontent_relation as P, content as C\n" \
              "WHERE P.content_id = C.c_id AND P.user_id={};".format(flask_login.current_user.id)
    try:
        cursor = g.conn.execute(sql_cmd)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))
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
    try:
        cursor = g.conn.execute(scmd_01)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))
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
    if check_user_type() == 'True':
        return redirect(url_for('admin_event'))
    sql_cmd = "SELECT C.c_id as content_id, " \
              "(SELECT COUNT(L.user_id) FROM like_relation as L RIGHT JOIN content as C1 ON C1.c_id=L.content_id\n" \
              "WHERE C1.c_id=C.c_id) as likes, " \
              "C.image as image, C.text as text, P.user_id as user_id, U.name as name \n" \
              "FROM follow_relation as F, content as C, postcontent_relation as P, users as U \n" \
              "WHERE F.follower_id={} AND P.content_id=C.c_id AND P.user_id=F.following_id " \
              "AND U.user_id=F.following_id;".format(flask_login.current_user.id)

    try:
        cursor = g.conn.execute(sql_cmd)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))
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


@app.route('/admin_delete_event', methods=['POST'])
def admin_delete_event():
    event_id = request.form.get('event_id')
    scmd_1 = "DELETE FROM event WHERE e_id={} " \
             "AND EXISTS(SELECT * FROM publish_relation as P WHERE P.admin_id={} and P.e_id={});"\
        .format(event_id, flask_login.current_user.id, event_id)
    try:
        g.conn.execute(scmd_1)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))
    return redirect(url_for('admin_event'))


@app.route('/admin_event', methods=['GET'])
def admin_event():
    if check_user_type() == 'False':
        return redirect(url_for('admin_login'))
    admin_id = flask_login.current_user.get_id().split(' ')[0]
    #print(admin_id)
    scmd_1 = "SELECT E.e_id as e_id, A.addr_id as addr_id, " \
             "A.city as city, A.street as street, A.zipcode as zipcode," \
             "E.start_time as start_time, E.end_time as end_time\n" \
             "FROM event as E, at_relation as R, address as A, admin as D, publish_relation as P\n" \
             "WHERE E.e_id=R.e_id AND A.addr_id=R.addr_id AND D.admin_id={} " \
             "AND D.admin_id=P.admin_id AND E.e_id=P.e_id;".format(admin_id)
    try:
        cursor = g.conn.execute(scmd_1)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))
    events = []
    for result in cursor:
        content = dict()
        content['e_id'] = result['e_id']
        content['addr_id'] = result['addr_id']
        content['city'] = result['city']
        content['street'] = result['street']
        content['zipcode'] = result['zipcode']
        content['start_time'] = result['start_time']
        content['end_time'] = result['end_time']
        events.append(content)
    cursor.close()
    context = dict(data=events)
    return render_template('admin_event.html', **context)



@app.route('/addEvent', methods=['GET', 'POST'])
def addEvent():
    def rollback_event(e_id):
        scmd = "DELETE FROM event WHERE e_id={}".format(e_id)
        try:
            g.conn.execute(scmd)
        except (Exception, psycopg2.Error, SystemError) as ex:
            return render_error(str(ex))

    def rollback_address(addr_id):
        scmd = "DELETE FROM address WHERE addr_id={}".format(addr_id)
        try:
            g.conn.execute(scmd)
        except (Exception, psycopg2.Error, SystemError) as ex:
            return render_error(str(ex))


    if check_user_type() == 'False':
        return redirect(url_for('admin_login'))
    if request.method == 'GET':
        return render_template('add_event.html')
    else:
        d = request.form
        print(d)

        scmd_01 = "INSERT INTO event(start_time, end_time) " \
                  "VALUES({}, {}) RETURNING e_id".format(double_quote(d['start_date'] + ' ' + d['start_time']),
                                                         double_quote(d['end_date'] + ' ' + d['end_time']))
        try:
            cursor = g.conn.execute(scmd_01)
        except (Exception, psycopg2.Error, SystemError) as ex:
            return render_error(str(ex))

        row = cursor.fetchone()
        if not row:
            return render_error('Error in inserting into database')
        e_id = row['e_id']
        cursor.close()
        city, street, zipcode = d['city'], d['street'], d['zipcode']
        scmd_02 = "SELECT addr_id FROM address as A " \
                  "WHERE A.city={} AND A.street={} AND A.zipcode={}".format(double_quote(city),
                                                                            double_quote(street),
                                                                            double_quote(zipcode))
        try:
            cursor = g.conn.execute(scmd_02)
        except (Exception, psycopg2.Error, SystemError) as ex:
            print('rolling back database')
            rollback_event(e_id)
            return render_error(str(ex))

        row = cursor.fetchone()
        if row:
            addr_id = row['addr_id']
            cursor.close()
        else:
            cursor.close()
            scmd_03 = "INSERT INTO address(city, street, zipcode) " \
                      "VALUES({}, {}, {}) RETURNING addr_id".format(double_quote(city),
                                                  double_quote(street),
                                                  double_quote(zipcode))
            try:
                cursor = g.conn.execute(scmd_03)
            except (Exception, psycopg2.Error, SystemError) as ex:
                return render_error(str(ex))
            row = cursor.fetchone()
            if not row:
                print('rolling back database')
                rollback_event(e_id)
                return render_error('Insertion into address table failed')

            addr_id = row['addr_id']
            cursor.close()

        scmd_04 = "INSERT INTO at_relation(e_id, addr_id) VALUES({}, {})".format(e_id, addr_id)
        try:
            g.conn.execute(scmd_04)
        except (Exception, psycopg2.Error, SystemError) as ex:
            print('rolling back database')
            rollback_event(e_id)
            rollback_address(addr_id)
            return render_error(str(ex))

        scmd_05 = "INSERT INTO publish_relation(admin_id, e_id) VALUES({}, {})"\
            .format(flask_login.current_user.id, e_id)
        try:
            g.conn.execute(scmd_05)
        except (Exception, psycopg2.Error, SystemError) as ex:
            print('rolling back database')
            rollback_event(e_id)
            rollback_address(addr_id)
            # no need to roll back at_relation since it's deleted ON CASCADE
            return render_error(str(ex))


    return render_template('add_event.html', **dict())


def register_event(e_id, user_id):
    scmd_1 = "INSERT INTO register_relation(user_id, event_id) " \
             "VALUES ({}, {});".format(user_id, e_id)
    try:
        g.conn.execute(scmd_1)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))


@app.route('/event', methods=['GET'])
def event():
    if check_user_type() == 'True':
        return redirect(url_for('admin_event'))
    scmd_1 = "SELECT E.e_id as e_id, A.addr_id as addr_id, " \
             "A.city as city, A.street as street, A.zipcode as zipcode," \
             "E.start_time as start_time, E.end_time as end_time," \
             "(SELECT COUNT(*) FROM register_relation as R WHERE R.user_id={} and R.event_id=E.e_id) as counts\n" \
             "FROM event as E, at_relation as R, address as A\n" \
             "WHERE E.e_id=R.e_id AND A.addr_id=R.addr_id;".format(flask_login.current_user.id)
    try:
        cursor = g.conn.execute(scmd_1)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))
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
        content['has_registered'] = result['counts'] > 0
        events.append(content)
    cursor.close()
    context = dict(data=events)
    return render_template('event.html', **context)


@app.route('/event_user/<e_id>', methods=['GET'])
def event_user(e_id):
    scmd_1 = "SELECT U.name as name, U.user_id as user_id FROM register_relation R, users U "\
             "WHERE R.user_id=U.user_id AND R.event_id={};".format(e_id)
    try:
        cursor = g.conn.execute(scmd_1)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))
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
    try:
        cursor = g.conn.execute(scmd_1, text)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))
    row = cursor.fetchone()
    if not row:
        return render_error('Error in inserting into comments table')
    cursor.close()

    c_id = row['c_id']
    scmd_1_del = "DELETE FROM comments WHERE c_id={};".format(c_id)
    scmd_2 = "INSERT INTO postcomment_relation(user_id, comment_id) " \
             "VALUES ({}, {});".format(flask_login.current_user.id, c_id)
    try:
        g.conn.execute(scmd_2)
    except (Exception, psycopg2.Error, SystemError) as ex:
        print('rollback database')
        g.conn.execute(scmd_1_del)
        return render_error(str(ex))


    scmd_2_del = "DELETE FROM postcomment_relation " \
                 "WHERE user_id={}, comment_id={};".format(flask_login.current_user.id, c_id)
    scmd_3 = "INSERT INTO commentat_relation(comment_id, content_id, time)" \
             "VALUES ({}, {}, {});".format(c_id, content_id, double_quote(time_now()))
    try:
        g.conn.execute(scmd_3)
    except (Exception, psycopg2.Error, SystemError) as ex:
        print('rollback database')
        g.conn.execute(scmd_1_del)
        g.conn.execute(scmd_2_del)
        return render_error(str(ex))

    return redirect(url_for('show', c_id = content_id))



@app.route('/addContent', methods=['POST'])
def addContent():
    image = request.form.get('image')
    text = request.form.get('text')
    '''
    image = double_quote(image)
    text = double_quote(text)
    scmd_1 = "INSERT INTO content(image, text) " \
             "VALUES ({}, {}) RETURNING c_id;".format(image, text)
    cursor = g.conn.execute(scmd_1)
    '''
    scmd_1 = "INSERT INTO content(image, text) " \
             "VALUES (%s, %s) RETURNING c_id;"
    try:
        cursor = g.conn.execute(scmd_1, image, text)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))
    row = cursor.fetchone()
    if not row:
        return render_error('Error in inserting into content table')
    c_id = row['c_id']
    cursor.close()
    scmd_1_del = "DELETE FROM content WHERE c_id={}".format(c_id)
    scmd_2 = "INSERT INTO postcontent_relation(content_id, user_id, time) " \
             "VALUES ({}, {}, {});".format(c_id, flask_login.current_user.id, double_quote(time_now()))

    try:
        g.conn.execute(scmd_2)
    except (Exception, psycopg2.Error, SystemError) as ex:
        print('rollback database')
        g.conn.execute(scmd_1_del)
        return render_error(str(ex))

    return redirect(url_for('profile'))


@app.route('/addLike', methods=['POST'])
def addLike():
    content_id = request.form.get('content_id')
    scmd_1 = "INSERT INTO like_relation(user_id, content_id) " \
             "VALUES ({}, {});".format(flask_login.current_user.id, content_id)
    try:
        g.conn.execute(scmd_1)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))
    return redirect(url_for('show', c_id = content_id))


@app.route('/addFollowing', methods=['POST'])
def addFollowing():
    following_id = request.form.get('user_id')
    scmd_1 = "INSERT INTO follow_relation(following_id, follower_id) " \
             "VALUES ({}, {});".format(following_id, flask_login.current_user.id)
    try:
        g.conn.execute(scmd_1)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))
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
    try:
        g.conn.execute(scmd_02)
        g.conn.execute(scmd_01)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))
    return redirect(url_for('profile'))



@app.route('/deleteFollowing', methods=['POST'])
def deleteFollowing():
    following_id = request.form.get('user_id')
    scmd_01 = "DELETE FROM follow_relation " \
              "WHERE follower_id={} and following_id={};".format(flask_login.current_user.id, following_id)
    try:
        g.conn.execute(scmd_01)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))
    return redirect(url_for('following'))



@app.route('/modifyCategory', methods=['POST'])
def modifyCategory():
    temp_dict = request.form.lists()
    selectedCategory = temp_dict[0][1]

    user_id = flask_login.current_user.id
    scmd_01 = "DELETE FROM belongto_relation " \
              "WHERE user_id={};".format(user_id)
    try:
        g.conn.execute(scmd_01)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))

    values = ['({}, {})'.format(user_id, c_id) for c_id in selectedCategory]
    scmd_02 = "INSERT INTO belongto_relation(user_id, c_id) " \
              "VALUES {};".format(', '.join(values))
    try:
        g.conn.execute(scmd_02)
    except (Exception, psycopg2.Error, SystemError) as ex:
        return render_error(str(ex))
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
                msg = 'duplicate name detected, use a different name'
                return render_template('register.html', error=msg)


            # use this to get auto-incremented primary key value
            cursor = g.conn.execute("INSERT INTO users(date_of_birth, pwd, name) \n"
                                    "VALUES (%s, %s, %s) RETURNING user_id;", (dateOfBirth, password, username))
            row = cursor.fetchone()
            if not row:
                return render_error('Registering user failed')

            print('Created user with id {}'.format(row['user_id']))
            return redirect(url_for('login'))

        except Exception as e:
            print(e)
            msg = 'error occured in executing SQL command'
            return render_template('register.html', error=msg)

    else:
        return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        try:
            cursor = g.conn.execute("SELECT * FROM users WHERE name=%s AND pwd=%s;", (username, password))
        except (Exception, psycopg2.Error, SystemError) as ex:
            return render_error(str(ex))

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


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        try:
            cursor = g.conn.execute("SELECT * FROM admin WHERE name=%s AND pwd=%s;", (username, password))
        except (Exception, psycopg2.Error, SystemError) as ex:
            return render_error(str(ex))

        row = cursor.fetchone()
        cursor.close()
        if row:
            user = User(row['admin_id'], row['name'], True)
            print(row['admin_id'], row['name'], row['pwd'], 'Admin')
            flask_login.login_user(user)
            print("Successfully login")

            return redirect(url_for("admin_event"))

        else:
            error = 'Invalid username or password. Please try again!'
            flash(error)
            return render_template('admin_login.html')

    else:
        return render_template("admin_login.html")



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
