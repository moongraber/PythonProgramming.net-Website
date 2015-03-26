from flask import Flask, render_template, redirect, \
    url_for, request, session, flash, g, make_response
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from functools import wraps
import MySQLdb
from MySQLdb import escape_string as thwart
import json

import datetime
from time import mktime
import os
import time
import urllib2
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from werkzeug.security import generate_password_hash, \
     check_password_hash
from passlib.hash import sha256_crypt
from dbconnect import connection
import gc
# Dictates urls and linkage
from content_management import Content




try:
    c,conn = connection()
    data = c.execute("SELECT uid, username, tracking FROM users")
    data = c.fetchall()

    total_users = len(data)

    total_completed_tutorials = 0

    for d in data:
        tracking = d[2]
        split_t = tracking.split(',')
        total_complete = len(split_t)
        total_completed_tutorials += total_complete

    average_completed = round(float(total_completed_tutorials) / total_users,2)

    c = open("/var/www/PythonProgramming/PythonProgramming/user-data-tracking.csv", "a")
    saveLine = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M')+","+str(round(time.time(),0))+","+str(total_users)+","+str(total_completed_tutorials)+","+str(average_completed)+'\n'
    c.write(saveLine)
    c.close()

except Exception as e:
    print(str(e))
