from flask import Flask, render_template, redirect, \
    url_for, request, session, flash, g, make_response
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from functools import wraps
import MySQLdb
from MySQLdb import escape_string as thwart
import json
import datetime
from datetime import datetime,timedelta
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
import smtplib



app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# list of topics by {TOPIC:["TITLE", "URL"]}
TOPIC_DICT = Content()


class User:
    def username(self):
        try:
            return str(session['username'])
        except:
            return("guest")

        
user = User()



    

def userinformation():
    try:
        client_name = (session['username'])
        guest = False
    except:
        guest = True
        client_name = "Guest"
        


    if not guest:
        try:
            
            c,conn = connection()
            c.execute("SELECT * FROM users WHERE username = (%s)",
                    (thwart(client_name)))
            data = c.fetchone()
            settings = data[4]
            tracking = data[5]
            rank = data[6]
            #flash(data)
        except Exception, e:
            pass
            #flash(str(e))

    else:
        settings = [0,0]
        tracking = [0,0]
        rank = [0,0]


    return client_name, settings, tracking, rank


def update_user_tracking():
    try:
        completed = str(request.args['completed'])

        if completed in str(TOPIC_DICT.values()):
            #flash("shes in here!")
            #flash(completed)
            client_name, settings, tracking, rank = userinformation()

            #flash(str(client_name))
            #flash(str(tracking))

            

            if tracking == None:
                tracking = completed
            else:
                if completed not in tracking:
                    tracking = tracking+","+completed
            
            c,conn = connection()
            c.execute("UPDATE users SET tracking = %s WHERE username = %s",
                    (thwart(tracking),thwart(client_name)))
            conn.commit()
            c.close()
            conn.close()
            client_name, settings, tracking, rank = userinformation()

            #flash(str(client_name))
            #flash(str(tracking))
        else:
            pass
            #flash("that shit aint here boss")
            #flash(completed)
            
    except Exception, e:
        pass
        #flash(str(e))


class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=20)])
    email = TextField('Email Address', [validators.Length(min=6, max=50)])
    password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the <a href="/about/tos" target="blank">Terms of Service</a> and <a href="/about/privacy-policy" target="blank">Privacy Notice</a> (updated Jan 22, 2015)', [validators.Required()])
    

## LIVE VERSION ####
@app.route('/robots.txt/')
def robots():
    return("User-agent: *\nDisallow: /register/\nDisallow: /login/\nDisallow: /donation-success/")


###### DEV VERSION #####
##@app.route('/robots.txt/')
##def robots():
##    return("User-agent: *\nDisallow: /")
##




@app.route('/sitemap.xml', methods=['GET'])
def sitemap():
    try:
      """Generate sitemap.xml. Makes a list of urls and date modified."""
      pages=[]
      ten_days_ago=(datetime.now() - timedelta(days=7)).date().isoformat()
      # static pages
      for rule in app.url_map.iter_rules():
          if "GET" in rule.methods and len(rule.arguments)==0:
              pages.append(
                           ["http://pythonprogramming.net"+str(rule.rule),ten_days_ago]
                           )

      sitemap_xml = render_template('sitemap_template.xml', pages=pages)
      response= make_response(sitemap_xml)
      response.headers["Content-Type"] = "application/xml"    
    
      return response
    except Exception as e:
        return(str(e))



def dataGeneration(clientData):

    total_users_list = []
    total_completed_tutorials_list = []

    avg_tuts_list = []
    
    for eachLine in clientData[1:]:
        FundPset = []
        marketPset = []
        bitcoinSet = []
        avgtutset = []
        
        splitLine = eachLine.split(',')
        timeStamp = float(splitLine[1])*1000
        total_completed_tutorials = float(splitLine[3])

        total_users =  int(splitLine[2])

        avgTuts = float(splitLine[-1].replace('\n',''))



        marketPset.append(timeStamp)
        marketPset.append(total_users)

        bitcoinSet.append(timeStamp)
        bitcoinSet.append(total_completed_tutorials)


        avgtutset.append(timeStamp)
        avgtutset.append(avgTuts)
        
    
        avg_tuts_list.append(avgtutset)
        total_users_list.append(marketPset)
        total_completed_tutorials_list.append(bitcoinSet)

    return total_users_list,total_completed_tutorials_list,avg_tuts_list


@app.route('/graph-user-tracking/')
def graph_users(chartID = 'chart_ID', chart_type = 'line', chart_height = 500):
    if session['username'].title() == "Harrison":
        try:
            clientData = open("/var/www/PythonProgramming/PythonProgramming/user-data-tracking.csv","r").readlines()
            chart = {"renderTo": chartID, "type": chart_type, "height": chart_height, "zoomType":'x'}
            totsusers,totstutscomps,avg_tuts_list = dataGeneration(clientData)

            
            series = [{"name": 'Total Users', "data": totsusers},{"name": 'Total completed Tuts', "data": totstutscomps, "yAxis":1},{"name": 'Avg Tuts / user', "data": avg_tuts_list, "yAxis":2}]
            title = {"text": 'Fund Performance compared to Market'}
            xAxis = {"type":"datetime"}
            yAxis = [{"title": {"text": 'Total Users'}},{ "title": {"text": 'Total Completed Tutorials'}} ,{ "title": {"text": 'Avg Tutorials / user'},"opposite":"true" }]#,"opposite":"true" } ]
##            c,conn = connection()
##            data = c.execute("SELECT uid, username, tracking FROM users")
##            data = c.fetchall()
##
##            data = list(data)
##            data = [list(i) for i in data]
##
##            for d in data:
##                d[2] = d[2].split(",")
##                d[2] = len(d[2])

            return render_template('usertracking.html', chartID=chartID, chart=chart, series=series, title=title, xAxis=xAxis, yAxis=yAxis)
        except Exception as e:
            return(str(e))
    else:
        return redirect(url_for('dashboard')) 



def index(chartID = 'chart_ID', chart_type = 'bar', chart_height = 350):
	chart = {"renderTo": chartID, "type": chart_type, "height": chart_height,}
	series = [{"name": 'Label1', "data": [1,2,3]}, {"name": 'Label2', "data": [4, 5, 6]}]
	title = {"text": 'My Title'}
	xAxis = {"categories": ['xAxis Data1', 'xAxis Data2', 'xAxis Data3']}
	yAxis = {"title": {"text": 'yAxis Label'}}
	return render_template('index.html', chartID=chartID, chart=chart, series=series, title=title, xAxis=xAxis, yAxis=yAxis)
 


    


@app.route('/', methods=['GET', 'POST'])
def main():
    form = RegistrationForm(request.form)
    try:
        c,conn = connection()
        error = None
        if request.method == 'POST':
            try:
                data = c.execute("SELECT * FROM users WHERE username = (%s)",
                        thwart(request.form['username']))
                data = c.fetchone()[2]

                if sha256_crypt.verify(request.form['password'], data):
                    session['logged_in'] = True
                    session['username'] = request.form['username']
                    flash('You are now logged in.')
                    return redirect(url_for('dashboard'))
            except Exception, e:
                flash("What are you doing?")


            try:
                
                if request.method == 'POST' and form.validate():

                    username = form.username.data
                    email = form.email.data

                    password = sha256_crypt.encrypt((str(form.password.data)))
                    c,conn = connection()

                    x = c.execute("SELECT * FROM users WHERE username = (%s)",
                        (thwart(username)))

                    if int(x) > 0:
                        flash("That username is already taken, please choose another")
                        return render_template('register.html', form=form)

                    else:
                        c.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                            (thwart(username), thwart(password), thwart(email)))
                        conn.commit()
                        flash('Thanks for registering')
                        c.close()
                        conn.close()
                        gc.collect()
                        session['logged_in'] = True
                        session['username'] = username
                        return redirect(url_for('dashboard'))

            except Exception as e:
                return(str(e))
  
            else:
                flash('Invalid credentials. Try again')
        gc.collect()
        return render_template("main.html", error=error, form=form, page_type = "main")
    except Exception, e:
        return(str(e))


@app.route('/brythoneditor/')
def brythoneditor():
    try:
        gc.collect()
        return render_template("brythoneditor.html")
    except Exception, e:
        return(str(e))

@app.route('/googled4c03d669c9855ca.html')
def google_confirm():
    try:
        gc.collect()
        return render_template("googled4c03d669c9855ca.html")
    except Exception, e:
        return(str(e))

@app.route('/trinket-challenge/')
def trinket_challenge():
    try:
        gc.collect()
        return render_template("trinket/trinketchallenge.html")
    except Exception, e:
        return(str(e))

@app.route('/trinket-editor/')
def trinket():
    try:
        gc.collect()
        return render_template("trinket/trinketeditor.html")
    except Exception, e:
        return(str(e))


@app.route('/editor/')
def editor():
    try:
        gc.collect()
        return render_template("editor.html")
    except Exception, e:
        return(str(e))


@app.route('/interactive-tutorials/', methods=['GET','POST'])
def i_editor():
    try:


        
        # success = green
        # info = blue
        # warning = yellow
        # danger = red
        #http://104.236.221.91/interactive-editor/?tutorial=%22beginner%22&submitted=%22tester%22&part=1

        informative_dict = {1:["This page offers you an interactive method for learning Python concepts, completely at your own pace!",
                         "Your general task will be explained here, and you will try to complete the objective by using the editor below. To see if you've done it right, enter your code and click on the 'Run' button!"]}

        body_info = []
        hints = []

        try:
            t = str(request.args['topic'])
            p = int(request.args['part'])
            s = str(request.args['submitted'])
            a = int(request.args['attempts'])
            body_info = TOPIC_DICT[t][p][2]
            titl_info = TOPIC_DICT[t][p][0]
            #flash(["type","info","test"])

            if a == 1:
                flash(s)

        except Exception as e:
            # this means they just arrived to the editor, nothing more.
            body_info = informative_dict[1]
            titl_info = "Interactive Python Tutorials"

        init_value = ""
        gc.collect()
        return render_template("interactive-editor.html",init_value=init_value, body_info = body_info, title = titl_info, hints=hints)
    except Exception, e:
        return(str(e))


@app.route('/header.py')
def headerpython():
    try:
        gc.collect()
        return render_template("header.py")
    except Exception, e:
        return(str(e))




    
    

@app.errorhandler(404)
def page_not_found(e):
    try:
        gc.collect()
        rule = request.path


        if "feed" in rule or "favicon" in rule or "wp-content" in rule or "wp-login" in rule or "wp-login" in rule or "wp-admin" in rule or "xmlrpc" in rule or "tag" in rule or "wp-include" in rule or "style" in rule or "apple-touch" in rule or "genericons" in rule or "topics" in rule or "category" in rule or "index" in rule or "include" in rule or "trackback" in rule or "download" in rule or "viewtopic" in rule or "browserconfig" in rule:
            pass
        else:

            errorlogging = open("/var/www/PythonProgramming/PythonProgramming/fourohfour","a")
            errorlogging.write((str(rule)+'\n'))
        #flash(str(rule))
        return render_template('404.html'), 404
    except Exception as e:
        return(str(e))

@app.errorhandler(500)
def page_not_found(e):
    return ("Ouch, looks like we're knocked out"), 500


# login required decorator
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap


@app.route('/user/change-password/', methods=['GET', 'POST'])
@login_required
def change_password():
    try:
        c,conn = connection()
        
        error = None
        if request.method == 'POST':

            data = c.execute("SELECT * FROM users WHERE username = (%s)",
                    thwart(user.username()))
            data = c.fetchone()[2]


            if sha256_crypt.verify(request.form['password'], data):
                flash('Authentication Successful.')
                if len(request.form['npassword']) > 0:
                    #flash("You wanted to change password")
                    
                    if request.form['npassword'] == request.form['rnpassword'] and len(request.form['npassword']) > 0:
                        try:
                            #flash("new passwords matched")
                            password = sha256_crypt.encrypt((str(request.form['npassword'])))
                            
                            c,conn = connection()
                            
                            data = c.execute("UPDATE users SET password = %s where username = %s",
                            (password,thwart(user.username())))

                            conn.commit()
                            c.close()
                            conn.close()
                            flash("Password changed")
                        except Exception, e:
                            return(str(e))
                    else:
                        flash("Passwords do not match!")

                return render_template('change-password.html', name=user.username(), error=error)

            

            else:
                flash('Invalid credentials. Try again')
                error = 'Invalid credentials. Try again'
        gc.collect()          
        return render_template('change-password.html', name=user.username())#, error=error)
    except Exception, e:
        return(str(e))



@app.route('/login/', methods=['GET','POST'])
def login():
    try:
        c,conn = connection()
        
        error = None
        if request.method == 'POST':

            data = c.execute("SELECT * FROM users WHERE username = (%s)",
                    thwart(request.form['username']))
            data = c.fetchone()[2]

            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True
                session['username'] = request.form['username']
                #flash('You are now logged in.'+str(session['username']))
                return redirect(url_for('dashboard'))

            else:
                error = 'Invalid credentials. Try again'
        gc.collect()
        return render_template('login.html', error=error)
    except Exception, e:
        error = 'Invalid credentials. Try again'
        return render_template('login.html', error=error)

    

@app.route('/logout/')
def logout():
	session.pop('logged_in', None)
	session.clear()
	flash('You have been logged out.')
	gc.collect()
	return redirect(url_for('main'))


@app.route('/register/', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def register():

    try:
        form = RegistrationForm(request.form)
        if request.method == 'POST' and form.validate():
            #flash("register attempted")

            username = form.username.data
            email = form.email.data

            password = sha256_crypt.encrypt((str(form.password.data)))
            c,conn = connection()

            x = c.execute("SELECT * FROM users WHERE username = (%s)",
                (thwart(username)))

            if int(x) > 0:
                flash("That username is already taken, please choose another")
                return render_template('register.html', form=form)

            else:
                c.execute("INSERT INTO users (username, password, email, tracking) VALUES (%s, %s, %s, %s)",
                    (thwart(username), thwart(password), thwart(email), thwart("/introduction-to-python-programming/")))
                conn.commit()
                flash('Thanks for registering')
                c.close()
                conn.close()
                gc.collect()
                session['logged_in'] = True
		session['username'] = username
                return redirect(url_for('intro_to_py'))
        gc.collect()
        #flash("hi there.")
        return render_template('register.html', form=form)
    except Exception as e:
        return(str(e))


def topic_completion_percent():
    try:
        client_name, settings, tracking, rank = userinformation()

        try:
            tracking = tracking.split(",")
        except:
            pass

        if tracking == None:
            tracking = []
            #flash("tracking is none")

        completed_percentages = {}
        

        for each_topic in TOPIC_DICT:
            total = 0
            total_complete = 0
            
            for each in TOPIC_DICT[each_topic]:
                total += 1
                for done in tracking:
                    if done == each[1]:
                        total_complete += 1

            percent_complete = int(((total_complete*100)/total))

            completed_percentages[each_topic] = percent_complete

           

        return completed_percentages
    except:
        for each_topic in TOPIC_DICT:
            total = 0
            total_complete = 0
        

            completed_percentages[each_topic] = 0.0

        return completed_percentages
    
    

    

    pass
    #return basics,pygame,pyopengl,kivy,flask,django,mysql,sqlite,datamanip,dataviz,nltk,svm,clustering,imagerec,forexalgo,robotics,supercomp,tkinter
    
@app.route('/guided-tutorials/', methods=['GET', 'POST'])
@app.route('/topics/', methods=['GET', 'POST'])
@app.route('/begin/', methods=['GET', 'POST'])
@app.route('/python-programming-tutorials/', methods=['GET', 'POST'])
@app.route('/dashboard/', methods=['GET', 'POST'])
#@login_required
def dashboard():
    try:
        try:
            client_name, settings, tracking, rank = userinformation()
            if len(tracking) < 10:
                tracking = "/introduction-to-python-programming/"
            gc.collect()

            

            if client_name == "Guest":
                flash("Welcome Guest, feel free to browse content. Progress tracking is only available for Logged-in users.")
                tracking = ['None']


            
            update_user_tracking()

            completed_percentages = topic_completion_percent()


                
            return render_template("dashboard.html",topics = TOPIC_DICT, tracking = tracking, completed_percentages=completed_percentages)
        except Exception, e:
            return((str(e), "please report errors to hskinsley@gmail.com"))
    except Exception, e:
        return((str(e), "please report errors to hskinsley@gmail.com"))

@app.route('/about/')
def aboutmission():
    gc.collect()
    return render_template("footer/mission.html")

@app.route('/contact/')
def contact():
    gc.collect()
    return render_template("footer/contact.html")

@app.route('/about/super-powers/')
def superpowers():
    gc.collect()
    return render_template("footer/superpowers.html")

@app.route('/about/technology/')
def technology():
    gc.collect()
    return render_template("footer/technology.html")

@app.route('/about/tos/')
def terms():
    gc.collect()
    return render_template("footer/terms.html")

@app.route('/about/privacy-policy/')
def privacy():
    gc.collect()
    return render_template("footer/privacy.html")

@app.route('/support-us-info/')
@app.route('/support-donate/')
def donate():
    try:

        # title: [description, current_donated, target donated, donation link]


        #
        #
        #

        future_topics = {"More Machine Learning with Scikit-Learn":["Machine Learning with Scikit-Learn is a massive topic that we've only just begun to cover. There are many more algorithms to cover, as well as topics to apply them to.",
                                                                    220,2500,"https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=QGWP42XA7ZRK2"],
                         "Kivy App Development":["Kivy is a cross-platform ( Windows, Linux OS X, Android and iOS) GUI and Game development library, capable of creating multi-touch apps and games",
                                                 143,700,"https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=ARBEC7F336LMA"],
                         "Flask Web Development in-depth":["So far, we've covered the basics of Flask, though there is a lot more to cover. The next series for Flask will be a tutorial covering how to create either this website, or something similar.",
                                                           200,1500,"https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=EXFK2BYV4UBKL"],
                         "PyQT GUI development":["PyQT is a GUI development toolkit aimed at producing higher quality GUIs than something like Tkinter.",
                                                 25,1000,"https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=F8SH6WYBFP8J8"],
                         "Python for Finance":["Python makes for a fantastic data analysis language, and can do everything from financial analysis to back testing to live trading. This series will cover it all from start to finish.",
                                               520,2500,"https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=M3ZBJ6L9J54S8"],
                         "Robotics":["Python and the Raspberry Pi make for a great way to learn about and actually do robotics. This series will require you to buy the robotics parts, however.",
                                     120,1500,"https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=U9CTKCH9MCQCE"],
                         "Python/Programming for Entrepreneurs and Business":["This one hits close to home for me. I learned Python to start my own businesses and I have never looked back. This series will teach you the basics of starting and running an actual business using Python and Entrepreneurship",
                                                                  350,5500,"https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=MS3MCCMF5BHLQ"]}



        list_template = """
                                                      <a href="{{ future_topics[t][3] }}" class="list-group-item">
                                                            <h4 class="list-group-item-heading">{{ t }}</h4> 
                                                            <div class="progress">
                                                              <div class="progress-bar" role="progressbar" aria-valuenow="5" aria-valuemin="0" aria-valuemax="{{ future_topics[t][2] }}" style="width: {{ future_topics[t][2] / future_topics[t][3] }}%;">
                                                                            ${{ future_topics[t][2] }} / ${{ future_topics[t][3] }}&nbsp;&nbsp; {{ future_topics[t][2] /future_topics[t][3] }}%
                                                                    </div>
                                                            </div>
                                                            <p class="list-group-item-text">{{ future_topics[t][0] }}</p>
                                                      </a>
    """




        
        gc.collect()
        return render_template("footer/supportus.html", future_topics = future_topics, list_template = list_template)
    except Exception as e:
        return(str(e))


@app.route('/donation-success/')
def donate_success():
    try:
        msg = 'Got a donation success, check.'
        server = smtplib.SMTP('smtp.gmail.com',587) #port 587 or 465
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login('seaofbtc@gmail.com','Icecream303030')
        server.sendmail('seaofbtc@gmail.com','hskinsley@gmail.com',msg)
        server.close()
        return render_template("footer/donationsuccess.html")
    except Exception as e:
        return render_template("footer/donationsuccess.html")



### BEGIN BASICS TUTORIALS ###


@app.route('/beginner-python-programming-tutorials/', methods=['GET', 'POST'])
@app.route('/introduction-to-python-programming/', methods=['GET', 'POST'])
@app.route('/introduction-to-python-programming', methods=['GET', 'POST'])
def intro_to_py():
    try:
        form = RegistrationForm(request.form)        
        client_name, settings, tracking, rank = userinformation()
        completed_percentages = topic_completion_percent()
        return render_template("tutorials/basics/intro-to-python.html",completed_percentages=completed_percentages,form=form, topics = TOPIC_DICT, curLink = TOPIC_DICT["Basics"][0][1], curTitle=TOPIC_DICT["Basics"][0][0],  nextLink = TOPIC_DICT["Basics"][1][1], nextTitle = TOPIC_DICT["Basics"][1][0] )
    except Exception, e:
        return(str(e))

@app.route(TOPIC_DICT["Basics"][1][1], methods=['GET', 'POST'])
def print_func_and_strings():
    try:
        update_user_tracking()
        completed_percentages = topic_completion_percent()
        return render_template("tutorials/basics/print-function-and-strings.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][1][1], curTitle=TOPIC_DICT["Basics"][1][0],  nextLink = TOPIC_DICT["Basics"][2][1], nextTitle = TOPIC_DICT["Basics"][2][0])
    except Exception, e:
        return(str(e))
        
@app.route(TOPIC_DICT["Basics"][2][1], methods=['GET', 'POST'])
def math_basics_python_3_beginner_tutorial():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/math-basics-python-3-beginner-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][2][1], curTitle=TOPIC_DICT["Basics"][2][0],  nextLink = TOPIC_DICT["Basics"][3][1], nextTitle = TOPIC_DICT["Basics"][3][0])


@app.route(TOPIC_DICT["Basics"][3][1], methods=['GET', 'POST'])
def python_3_variables_tutorial():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/variables.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][3][1], curTitle=TOPIC_DICT["Basics"][3][0],  nextLink = TOPIC_DICT["Basics"][4][1], nextTitle = TOPIC_DICT["Basics"][4][0])


@app.route(TOPIC_DICT["Basics"][4][1], methods=['GET', 'POST'])
def python_3_while_loop_tutorial():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/while-loop.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][4][1], curTitle=TOPIC_DICT["Basics"][4][0],  nextLink = TOPIC_DICT["Basics"][5][1], nextTitle = TOPIC_DICT["Basics"][5][0])

@app.route(TOPIC_DICT["Basics"][5][1], methods=['GET', 'POST'])
def python_3_for_loop_tutorial():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/for-loop.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][5][1], curTitle=TOPIC_DICT["Basics"][5][0],  nextLink = TOPIC_DICT["Basics"][6][1], nextTitle = TOPIC_DICT["Basics"][6][0])

@app.route(TOPIC_DICT["Basics"][6][1], methods=['GET', 'POST'])
def if_statement():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/if-statement.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][6][1], curTitle=TOPIC_DICT["Basics"][6][0],  nextLink = TOPIC_DICT["Basics"][7][1], nextTitle = TOPIC_DICT["Basics"][7][0])

@app.route(TOPIC_DICT["Basics"][7][1], methods=['GET', 'POST'])
def if_else_statement():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/if-else-statement.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][7][1], curTitle=TOPIC_DICT["Basics"][7][0],  nextLink = TOPIC_DICT["Basics"][8][1], nextTitle = TOPIC_DICT["Basics"][8][0])

@app.route(TOPIC_DICT["Basics"][8][1], methods=['GET', 'POST'])
def if_elif_else():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/if_elif_else.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][8][1], curTitle=TOPIC_DICT["Basics"][8][0],  nextLink = TOPIC_DICT["Basics"][9][1], nextTitle = TOPIC_DICT["Basics"][9][0])

@app.route(TOPIC_DICT["Basics"][9][1], methods=['GET', 'POST'])
def py_functions():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/py_functions.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][9][1], curTitle=TOPIC_DICT["Basics"][9][0],  nextLink = TOPIC_DICT["Basics"][10][1], nextTitle = TOPIC_DICT["Basics"][10][0])

@app.route(TOPIC_DICT["Basics"][10][1], methods=['GET', 'POST'])
def function_parameters():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/function_parameters.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][10][1], curTitle=TOPIC_DICT["Basics"][10][0],  nextLink = TOPIC_DICT["Basics"][11][1], nextTitle = TOPIC_DICT["Basics"][11][0])

@app.route(TOPIC_DICT["Basics"][11][1], methods=['GET', 'POST'])
def function_parameter_defaults():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/function_parameter_defaults.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][11][1], curTitle=TOPIC_DICT["Basics"][11][0],  nextLink = TOPIC_DICT["Basics"][12][1], nextTitle = TOPIC_DICT["Basics"][12][0])

@app.route(TOPIC_DICT["Basics"][12][1], methods=['GET', 'POST'])
def Global_and_Local_Variables():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Global_and_Local_Variables.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][12][1], curTitle=TOPIC_DICT["Basics"][12][0],  nextLink = TOPIC_DICT["Basics"][13][1], nextTitle = TOPIC_DICT["Basics"][13][0])

@app.route(TOPIC_DICT["Basics"][13][1], methods=['GET', 'POST'])
def Installing_Modules():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Installing_Modules.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][13][1], curTitle=TOPIC_DICT["Basics"][13][0],  nextLink = TOPIC_DICT["Basics"][14][1], nextTitle = TOPIC_DICT["Basics"][14][0])

@app.route(TOPIC_DICT["Basics"][14][1], methods=['GET', 'POST'])
def modules_and_pip_install():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Install_Modules_with_Pip.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][14][1], curTitle=TOPIC_DICT["Basics"][14][0],  nextLink = TOPIC_DICT["Basics"][15][1], nextTitle = TOPIC_DICT["Basics"][15][0])

@app.route(TOPIC_DICT["Basics"][15][1], methods=['GET', 'POST'])
def Common_Errors():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Common_Errors.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][15][1], curTitle=TOPIC_DICT["Basics"][15][0],  nextLink = TOPIC_DICT["Basics"][16][1], nextTitle = TOPIC_DICT["Basics"][16][0])

@app.route(TOPIC_DICT["Basics"][16][1], methods=['GET', 'POST'])
def Writing_to_a_File():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Writing_to_a_File.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][16][1], curTitle=TOPIC_DICT["Basics"][16][0],  nextLink = TOPIC_DICT["Basics"][17][1], nextTitle = TOPIC_DICT["Basics"][17][0])

@app.route(TOPIC_DICT["Basics"][17][1], methods=['GET', 'POST'])
def Appending_Files():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Appending_Files.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][17][1], curTitle=TOPIC_DICT["Basics"][17][0],  nextLink = TOPIC_DICT["Basics"][18][1], nextTitle = TOPIC_DICT["Basics"][18][0])

@app.route(TOPIC_DICT["Basics"][18][1], methods=['GET', 'POST'])
def Reading_from_Files():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Reading_from_Files.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][18][1], curTitle=TOPIC_DICT["Basics"][18][0],  nextLink = TOPIC_DICT["Basics"][19][1], nextTitle = TOPIC_DICT["Basics"][19][0])

@app.route(TOPIC_DICT["Basics"][19][1], methods=['GET', 'POST'])
def Classes():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Classes.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][19][1], curTitle=TOPIC_DICT["Basics"][19][0],  nextLink = TOPIC_DICT["Basics"][20][1], nextTitle = TOPIC_DICT["Basics"][20][0])

@app.route(TOPIC_DICT["Basics"][20][1], methods=['GET', 'POST'])
def Frequently_asked_Questions():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Frequently_asked_Questions.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][20][1], curTitle=TOPIC_DICT["Basics"][20][0],  nextLink = TOPIC_DICT["Basics"][21][1], nextTitle = TOPIC_DICT["Basics"][21][0])

@app.route(TOPIC_DICT["Basics"][21][1], methods=['GET', 'POST'])
def Getting_User_Input():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Getting_User_Input.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][21][1], curTitle=TOPIC_DICT["Basics"][21][0],  nextLink = TOPIC_DICT["Basics"][22][1], nextTitle = TOPIC_DICT["Basics"][22][0])

@app.route(TOPIC_DICT["Basics"][22][1], methods=['GET', 'POST'])
def Statistics_Module():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Statistics_Module.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][22][1], curTitle=TOPIC_DICT["Basics"][22][0],  nextLink = TOPIC_DICT["Basics"][23][1], nextTitle = TOPIC_DICT["Basics"][23][0])

@app.route(TOPIC_DICT["Basics"][23][1], methods=['GET', 'POST'])
def Module_import_Syntax():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Module_import_Syntax.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][23][1], curTitle=TOPIC_DICT["Basics"][23][0],  nextLink = TOPIC_DICT["Basics"][24][1], nextTitle = TOPIC_DICT["Basics"][24][0])

@app.route(TOPIC_DICT["Basics"][24][1], methods=['GET', 'POST'])
def Making_your_own_Modules():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Making_your_own_Modules.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][24][1], curTitle=TOPIC_DICT["Basics"][24][0],  nextLink = TOPIC_DICT["Basics"][25][1], nextTitle = TOPIC_DICT["Basics"][25][0])

@app.route(TOPIC_DICT["Basics"][25][1], methods=['GET', 'POST'])
def Python_Lists_vs_Tuples():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Python_Lists_vs_Tuples.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][25][1], curTitle=TOPIC_DICT["Basics"][25][0],  nextLink = TOPIC_DICT["Basics"][26][1], nextTitle = TOPIC_DICT["Basics"][26][0])

@app.route(TOPIC_DICT["Basics"][26][1], methods=['GET', 'POST'])
def List_Manipulation():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/List_Manipulation.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][26][1], curTitle=TOPIC_DICT["Basics"][26][0],  nextLink = TOPIC_DICT["Basics"][27][1], nextTitle = TOPIC_DICT["Basics"][27][0])

@app.route(TOPIC_DICT["Basics"][27][1], methods=['GET', 'POST'])
def Multi_dimensional_lists():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Multi_dimensional_lists.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][27][1], curTitle=TOPIC_DICT["Basics"][27][0],  nextLink = TOPIC_DICT["Basics"][28][1], nextTitle = TOPIC_DICT["Basics"][28][0])

@app.route(TOPIC_DICT["Basics"][28][1], methods=['GET', 'POST'])
def Reading_CSV_files_in_Python():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Reading_CSV_files_in_Python.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][28][1], curTitle=TOPIC_DICT["Basics"][28][0],  nextLink = TOPIC_DICT["Basics"][29][1], nextTitle = TOPIC_DICT["Basics"][29][0])

@app.route(TOPIC_DICT["Basics"][29][1], methods=['GET', 'POST'])
def Try_and_Except_Error_handling():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Try_and_Except_Error_handling.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][29][1], curTitle=TOPIC_DICT["Basics"][29][0],  nextLink = TOPIC_DICT["Basics"][30][1], nextTitle = TOPIC_DICT["Basics"][30][0])

@app.route(TOPIC_DICT["Basics"][30][1], methods=['GET', 'POST'])
def Multi_Line_printing():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Multi_Line_printing.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][30][1], curTitle=TOPIC_DICT["Basics"][30][0],  nextLink = TOPIC_DICT["Basics"][31][1], nextTitle = TOPIC_DICT["Basics"][31][0])

@app.route(TOPIC_DICT["Basics"][31][1], methods=['GET', 'POST'])
def Python_dictionaries():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Python_dictionaries.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][31][1], curTitle=TOPIC_DICT["Basics"][31][0],  nextLink = TOPIC_DICT["Basics"][32][1], nextTitle = TOPIC_DICT["Basics"][32][0])

@app.route(TOPIC_DICT["Basics"][32][1], methods=['GET', 'POST'])
def Built_in_functions():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Built_in_functions.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][32][1], curTitle=TOPIC_DICT["Basics"][32][0],  nextLink = TOPIC_DICT["Basics"][33][1], nextTitle = TOPIC_DICT["Basics"][33][0])

@app.route(TOPIC_DICT["Basics"][33][1], methods=['GET', 'POST'])
def OS_Module():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/OS_Module.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][33][1], curTitle=TOPIC_DICT["Basics"][33][0],  nextLink = TOPIC_DICT["Basics"][34][1], nextTitle = TOPIC_DICT["Basics"][34][0])

@app.route(TOPIC_DICT["Basics"][34][1], methods=['GET', 'POST'])
def SYS_module():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/SYS_module.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][34][1], curTitle=TOPIC_DICT["Basics"][34][0],  nextLink = TOPIC_DICT["Basics"][35][1], nextTitle = TOPIC_DICT["Basics"][35][0])

@app.route(TOPIC_DICT["Basics"][35][1], methods=['GET', 'POST'])
def urllib_module():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/urllib_module.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][35][1], curTitle=TOPIC_DICT["Basics"][35][0],  nextLink = TOPIC_DICT["Basics"][36][1], nextTitle = TOPIC_DICT["Basics"][36][0])

@app.route(TOPIC_DICT["Basics"][36][1], methods=['GET', 'POST'])
def regular_expressions_with_re():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/regular_expressions_with_re.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][36][1], curTitle=TOPIC_DICT["Basics"][36][0],  nextLink = TOPIC_DICT["Basics"][37][1], nextTitle = TOPIC_DICT["Basics"][37][0])

@app.route(TOPIC_DICT["Basics"][37][1], methods=['GET', 'POST'])
def How_to_Parse_a_Website_with_regex_and_urllib():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/How_to_Parse_a_Website_with_regex_and_urllib.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][37][1], curTitle=TOPIC_DICT["Basics"][37][0],  nextLink = TOPIC_DICT["Basics"][38][1], nextTitle = TOPIC_DICT["Basics"][38][0])

@app.route(TOPIC_DICT["Basics"][38][1], methods=['GET', 'POST'])
def Tkinter_intro():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Tkinter_intro.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][38][1], curTitle=TOPIC_DICT["Basics"][38][0],  nextLink = TOPIC_DICT["Basics"][39][1], nextTitle = TOPIC_DICT["Basics"][39][0])

@app.route(TOPIC_DICT["Basics"][39][1], methods=['GET', 'POST'])
def Tkinter_buttons():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Tkinter_buttons.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][39][1], curTitle=TOPIC_DICT["Basics"][39][0],  nextLink = TOPIC_DICT["Basics"][40][1], nextTitle = TOPIC_DICT["Basics"][40][0])

@app.route(TOPIC_DICT["Basics"][40][1], methods=['GET', 'POST'])
def Tkinter_event_handling():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Tkinter_event_handling.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][40][1], curTitle=TOPIC_DICT["Basics"][40][0],  nextLink = TOPIC_DICT["Basics"][41][1], nextTitle = TOPIC_DICT["Basics"][41][0])

@app.route(TOPIC_DICT["Basics"][41][1], methods=['GET', 'POST'])
def Tkinter_menu_bar():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Tkinter_menu_bar.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][41][1], curTitle=TOPIC_DICT["Basics"][41][0],  nextLink = TOPIC_DICT["Basics"][42][1], nextTitle = TOPIC_DICT["Basics"][42][0])

@app.route(TOPIC_DICT["Basics"][42][1], methods=['GET', 'POST'])
def Tkinter_images():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Tkinter_images.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][42][1], curTitle=TOPIC_DICT["Basics"][42][0],  nextLink = TOPIC_DICT["Basics"][43][1], nextTitle = TOPIC_DICT["Basics"][43][0])

@app.route(TOPIC_DICT["Basics"][43][1], methods=['GET', 'POST'])
def Threading_module():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Threading_module.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][43][1], curTitle=TOPIC_DICT["Basics"][43][0],  nextLink = TOPIC_DICT["Basics"][44][1], nextTitle = TOPIC_DICT["Basics"][44][0])

@app.route(TOPIC_DICT["Basics"][44][1], methods=['GET', 'POST'])
def CX_Freeze():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/CX_Freeze.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][44][1], curTitle=TOPIC_DICT["Basics"][44][0],  nextLink = TOPIC_DICT["Basics"][45][1], nextTitle = TOPIC_DICT["Basics"][45][0])

@app.route(TOPIC_DICT["Basics"][45][1], methods=['GET', 'POST'])
def The_Subprocess_Module():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/The_Subprocess_Module.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][45][1], curTitle=TOPIC_DICT["Basics"][45][0],  nextLink = TOPIC_DICT["Basics"][46][1], nextTitle = TOPIC_DICT["Basics"][46][0])



@app.route("/downloads/style.zip", methods=['GET', 'POST'])
@app.route("/horizonal-bar-chart-python-matplotlib/", methods=['GET', 'POST'])
@app.route("/matplotlib-styles-tutorial/", methods=['GET', 'POST'])
@app.route("/customizing-bar-chart-matplotlib/", methods=['GET', 'POST'])
@app.route("/matplotlib-basics-first-graph/", methods=['GET', 'POST'])
@app.route("/matplotlib-graphing-series/", methods=['GET', 'POST'])
@app.route(TOPIC_DICT["Basics"][46][1], methods=['GET', 'POST'])
def Matplotlib_Crash_Course():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/Matplotlib_Crash_Course.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][46][1], curTitle=TOPIC_DICT["Basics"][46][0],  nextLink = TOPIC_DICT["Basics"][47][1], nextTitle = TOPIC_DICT["Basics"][47][0])



@app.route(TOPIC_DICT["Basics"][47][1], methods=['GET', 'POST'])
def ftplib_module():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/ftplib_module.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][47][1], curTitle=TOPIC_DICT["Basics"][47][0],  nextLink = TOPIC_DICT["Basics"][48][1], nextTitle = TOPIC_DICT["Basics"][48][0])

@app.route(TOPIC_DICT["Basics"][48][1], methods=['GET', 'POST'])
def Sockets():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/python-sockets.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][48][1], curTitle=TOPIC_DICT["Basics"][48][0],  nextLink = TOPIC_DICT["Basics"][49][1], nextTitle = TOPIC_DICT["Basics"][49][0])

@app.route(TOPIC_DICT["Basics"][49][1], methods=['GET', 'POST'])
def Simple_port_scanner_with_sockets():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/python-port-scanner-sockets.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][49][1], curTitle=TOPIC_DICT["Basics"][49][0],  nextLink = TOPIC_DICT["Basics"][50][1], nextTitle = TOPIC_DICT["Basics"][50][0])

@app.route(TOPIC_DICT["Basics"][50][1], methods=['GET', 'POST'])
def Threaded_port_scanner():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/python-threaded-port-scanner.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][50][1], curTitle=TOPIC_DICT["Basics"][50][0],  nextLink = TOPIC_DICT["Basics"][51][1], nextTitle = TOPIC_DICT["Basics"][51][0])

@app.route(TOPIC_DICT["Basics"][51][1], methods=['GET', 'POST'])
def Binding_and_listening_with_sockets():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/python-binding-listening-sockets.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][51][1], curTitle=TOPIC_DICT["Basics"][51][0],  nextLink = TOPIC_DICT["Basics"][52][1], nextTitle = TOPIC_DICT["Basics"][52][0])

@app.route(TOPIC_DICT["Basics"][52][1], methods=['GET', 'POST'])
def client_server_system_with_sockets():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/client-server-python-sockets.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][52][1], curTitle=TOPIC_DICT["Basics"][52][0],  nextLink = TOPIC_DICT["Basics"][53][1], nextTitle = TOPIC_DICT["Basics"][53][0])

@app.route(TOPIC_DICT["Basics"][53][1], methods=['GET', 'POST'])
def Python_2to3_for_converting_Python_2_scripts_to_Python_3():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/basics/converting-python2-to-python3-2to3.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Basics"][53][1], curTitle=TOPIC_DICT["Basics"][53][0],  nextLink = '/dashboard/', nextTitle = 'Back to the Dashboard')
### END BASICS TUTORIALS ###






### BEGIN SQLITE TUTORIALS ###
@app.route(TOPIC_DICT["SQLite"][0][1], methods=['GET', 'POST'])
def Inserting_into_a_Database():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/SQLite/sql-database-python-part-1-inserting-database.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["SQLite"][0][1], curTitle=TOPIC_DICT["SQLite"][0][0],  nextLink = TOPIC_DICT["SQLite"][1][1], nextTitle = TOPIC_DICT["SQLite"][1][0])




@app.route(TOPIC_DICT["SQLite"][1][1], methods=['GET', 'POST'])
def Dynamically_Inserting_into_a_Database():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/SQLite/sqlite-part-2-dynamically-inserting-database-timestamps.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["SQLite"][1][1], curTitle=TOPIC_DICT["SQLite"][1][0],  nextLink = TOPIC_DICT["SQLite"][2][1], nextTitle = TOPIC_DICT["SQLite"][2][0])




@app.route(TOPIC_DICT["SQLite"][2][1], methods=['GET', 'POST'])
def Read_from_Database():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/SQLite/sqlite-part-3-reading-database-python.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["SQLite"][2][1], curTitle=TOPIC_DICT["SQLite"][2][0],  nextLink = TOPIC_DICT["SQLite"][3][1], nextTitle = TOPIC_DICT["SQLite"][3][0])




@app.route(TOPIC_DICT["SQLite"][3][1], methods=['GET', 'POST'])
def Graphing_example_from_SQLite():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/SQLite/graphing-from-sqlite-database.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["SQLite"][3][1], curTitle=TOPIC_DICT["SQLite"][3][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")

### END SQLITE TUTORIALS ###


### BEGIN SUPERCOMPUTER TUTORIALS ###
@app.route(TOPIC_DICT["Build a Supercomputer and program with MPI"][0][1], methods=['GET', 'POST'])
def Build_a_Supercomputer_with_Raspberry_Pis():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Build a Supercomputer and program with MPI/build-supercomputer-raspberry-pi.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][0][1], curTitle=TOPIC_DICT["Build a Supercomputer and program with MPI"][0][0],  nextLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][1][1], nextTitle = TOPIC_DICT["Build a Supercomputer and program with MPI"][1][0])




@app.route(TOPIC_DICT["Build a Supercomputer and program with MPI"][1][1], methods=['GET', 'POST'])
def Intro():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Build a Supercomputer and program with MPI/supercomputer-intro.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][1][1], curTitle=TOPIC_DICT["Build a Supercomputer and program with MPI"][1][0],  nextLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][2][1], nextTitle = TOPIC_DICT["Build a Supercomputer and program with MPI"][2][0])




@app.route(TOPIC_DICT["Build a Supercomputer and program with MPI"][2][1], methods=['GET', 'POST'])
def Supplies():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Build a Supercomputer and program with MPI/supplies-for-supercomputer.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][2][1], curTitle=TOPIC_DICT["Build a Supercomputer and program with MPI"][2][0],  nextLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][3][1], nextTitle = TOPIC_DICT["Build a Supercomputer and program with MPI"][3][0])




@app.route(TOPIC_DICT["Build a Supercomputer and program with MPI"][3][1], methods=['GET', 'POST'])
def Installing_Operating_System():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Build a Supercomputer and program with MPI/installing-supercomputer-operating-system.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][3][1], curTitle=TOPIC_DICT["Build a Supercomputer and program with MPI"][3][0],  nextLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][4][1], nextTitle = TOPIC_DICT["Build a Supercomputer and program with MPI"][4][0])




@app.route(TOPIC_DICT["Build a Supercomputer and program with MPI"][4][1], methods=['GET', 'POST'])
def Downloading_and_installing_MPI():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Build a Supercomputer and program with MPI/download-and-install-mpi-for-supercomputer.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][4][1], curTitle=TOPIC_DICT["Build a Supercomputer and program with MPI"][4][0],  nextLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][5][1], nextTitle = TOPIC_DICT["Build a Supercomputer and program with MPI"][5][0])




@app.route("/copying-backing-master-node-win32-disk-imager/", methods=['GET', 'POST'])
@app.route(TOPIC_DICT["Build a Supercomputer and program with MPI"][5][1], methods=['GET', 'POST'])
def Testing_Supercomputer():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Build a Supercomputer and program with MPI/testing-supercomputer.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][5][1], curTitle=TOPIC_DICT["Build a Supercomputer and program with MPI"][5][0],  nextLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][6][1], nextTitle = TOPIC_DICT["Build a Supercomputer and program with MPI"][6][0])




@app.route(TOPIC_DICT["Build a Supercomputer and program with MPI"][6][1], methods=['GET', 'POST'])
def MPI_with_MPI4py_Introduction():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Build a Supercomputer and program with MPI/learning-use-mpi-python-mpi4py-module.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][6][1], curTitle=TOPIC_DICT["Build a Supercomputer and program with MPI"][6][0],  nextLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][7][1], nextTitle = TOPIC_DICT["Build a Supercomputer and program with MPI"][7][0])




@app.route(TOPIC_DICT["Build a Supercomputer and program with MPI"][7][1], methods=['GET', 'POST'])
def Installing_mpi4py_for_use_with_Python_and_MPI():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Build a Supercomputer and program with MPI/installing-testing-mpi4py-mpi-python-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][7][1], curTitle=TOPIC_DICT["Build a Supercomputer and program with MPI"][7][0],  nextLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][8][1], nextTitle = TOPIC_DICT["Build a Supercomputer and program with MPI"][8][0])




@app.route(TOPIC_DICT["Build a Supercomputer and program with MPI"][8][1], methods=['GET', 'POST'])
def First_basic_MPI_script_with_mpi4py_and_first_command_rank():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Build a Supercomputer and program with MPI/basic-mpi4py-script-getting-node-rank.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][8][1], curTitle=TOPIC_DICT["Build a Supercomputer and program with MPI"][8][0],  nextLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][9][1], nextTitle = TOPIC_DICT["Build a Supercomputer and program with MPI"][9][0])




@app.route(TOPIC_DICT["Build a Supercomputer and program with MPI"][9][1], methods=['GET', 'POST'])
def Using_conditional_Python_statements_alongside_MPI_commands_example():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Build a Supercomputer and program with MPI/conditional-statements-alongside-mpi-mpi4py.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][9][1], curTitle=TOPIC_DICT["Build a Supercomputer and program with MPI"][9][0],  nextLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][10][1], nextTitle = TOPIC_DICT["Build a Supercomputer and program with MPI"][10][0])




@app.route(TOPIC_DICT["Build a Supercomputer and program with MPI"][10][1], methods=['GET', 'POST'])
def Getting_network_processor_size_with_the_size_command():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Build a Supercomputer and program with MPI/mpi4py-size-command-mpi.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][10][1], curTitle=TOPIC_DICT["Build a Supercomputer and program with MPI"][10][0],  nextLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][11][1], nextTitle = TOPIC_DICT["Build a Supercomputer and program with MPI"][11][0])




@app.route(TOPIC_DICT["Build a Supercomputer and program with MPI"][11][1], methods=['GET', 'POST'])
def Sending_and_Receiving_data_using_send_and_recv_commands_with_MPI():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Build a Supercomputer and program with MPI/sending-receiving-data-messages-mpi4py.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][11][1], curTitle=TOPIC_DICT["Build a Supercomputer and program with MPI"][11][0],  nextLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][12][1], nextTitle = TOPIC_DICT["Build a Supercomputer and program with MPI"][12][0])




@app.route(TOPIC_DICT["Build a Supercomputer and program with MPI"][12][1], methods=['GET', 'POST'])
def Dynamically_sending_messages_to_and_from_processors_with_MPI_and_mpi4py():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Build a Supercomputer and program with MPI/sending-receiving-messages-nodes-dynamically.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][12][1], curTitle=TOPIC_DICT["Build a Supercomputer and program with MPI"][12][0],  nextLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][13][1], nextTitle = TOPIC_DICT["Build a Supercomputer and program with MPI"][13][0])




@app.route(TOPIC_DICT["Build a Supercomputer and program with MPI"][13][1], methods=['GET', 'POST'])
def Message_and_data_tagging_for_send_and_recv_MPI_commands_tutorial():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Build a Supercomputer and program with MPI/tagging-messages-mpi-multiple-messages.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][13][1], curTitle=TOPIC_DICT["Build a Supercomputer and program with MPI"][13][0],  nextLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][14][1], nextTitle = TOPIC_DICT["Build a Supercomputer and program with MPI"][14][0])




@app.route(TOPIC_DICT["Build a Supercomputer and program with MPI"][14][1], methods=['GET', 'POST'])
def MPI_broadcasting_tutorial_with_Python_mpi4py_and_bcast():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Build a Supercomputer and program with MPI/mpi-broadcast-tutorial-mpi4py.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][14][1], curTitle=TOPIC_DICT["Build a Supercomputer and program with MPI"][14][0],  nextLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][15][1], nextTitle = TOPIC_DICT["Build a Supercomputer and program with MPI"][15][0])




@app.route(TOPIC_DICT["Build a Supercomputer and program with MPI"][15][1], methods=['GET', 'POST'])
def Scatter_with_MPI_tutorial_with_mpi4py():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Build a Supercomputer and program with MPI/scatter-gather-mpi-mpi4py-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][15][1], curTitle=TOPIC_DICT["Build a Supercomputer and program with MPI"][15][0],  nextLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][16][1], nextTitle = TOPIC_DICT["Build a Supercomputer and program with MPI"][16][0])




@app.route(TOPIC_DICT["Build a Supercomputer and program with MPI"][16][1], methods=['GET', 'POST'])
def Gather_command_with_MPI_mpi4py_and_Python():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Build a Supercomputer and program with MPI/mpi-gather-command-mpi4py-python.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Build a Supercomputer and program with MPI"][16][1], curTitle=TOPIC_DICT["Build a Supercomputer and program with MPI"][16][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")

### END SUPERCOMPUTER TUTORIALS ###


### BEGIN MYSQL TUTORIALS ###
@app.route(TOPIC_DICT["MySQL"][0][1], methods=['GET', 'POST'])
def Intro_to_MySQL():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/MySQL/mysql-intro.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["MySQL"][0][1], curTitle=TOPIC_DICT["MySQL"][0][0],  nextLink = TOPIC_DICT["MySQL"][1][1], nextTitle = TOPIC_DICT["MySQL"][1][0])




@app.route(TOPIC_DICT["MySQL"][1][1], methods=['GET', 'POST'])
def Creating_Tables_and_Inserting_Data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/MySQL/create-mysql-tables-insert.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["MySQL"][1][1], curTitle=TOPIC_DICT["MySQL"][1][0],  nextLink = TOPIC_DICT["MySQL"][2][1], nextTitle = TOPIC_DICT["MySQL"][2][0])




@app.route(TOPIC_DICT["MySQL"][2][1], methods=['GET', 'POST'])
def Update_Select_and_Delete():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/MySQL/mysql-update-select-delete.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["MySQL"][2][1], curTitle=TOPIC_DICT["MySQL"][2][0],  nextLink = TOPIC_DICT["MySQL"][3][1], nextTitle = TOPIC_DICT["MySQL"][3][0])




@app.route(TOPIC_DICT["MySQL"][3][1], methods=['GET', 'POST'])
def Inserting_Variable_Data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/MySQL/mysql-insert-variable.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["MySQL"][3][1], curTitle=TOPIC_DICT["MySQL"][3][0],  nextLink = TOPIC_DICT["MySQL"][4][1], nextTitle = TOPIC_DICT["MySQL"][4][0])




@app.route(TOPIC_DICT["MySQL"][4][1], methods=['GET', 'POST'])
def Streaming_Tweets_from_Twitter_to_Database():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/MySQL/mysql-live-database-example-streaming-data.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["MySQL"][4][1], curTitle=TOPIC_DICT["MySQL"][4][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")
### END MYSQL TUTORIALS ###


@app.route("/use-twitter-api-v1-1-python-stream-tweets/", methods=['GET', 'POST'])
@app.route("/twitter-api-streaming-tweets-python-tutorial/", methods=['GET', 'POST'])
def Streaming_Tweets_from_Twitter_API():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/MySQL/streaming-from-twitter-api.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["MySQL"][4][1], curTitle=TOPIC_DICT["MySQL"][4][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")






### BEGIN SUPPORT VECTOR MACHINE TUTORIALS ###





@app.route("/sci-kit-learn-tutorials-machine-learning-python-investing/", methods=['GET', 'POST'])
@app.route("/scikit-learn-tutorials-machine-learning-python-investing/", methods=['GET', 'POST'])
@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][0][1], methods=['GET', 'POST'])
def Intro_to_Machine_Learning():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/machine-learning-intro.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][0][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][0][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][1][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][1][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][1][1], methods=['GET', 'POST'])
def Simple_Support_Vector_Machine_svm_example_with_character_recognition():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/support-vector-machine-svm-example-tutorial-scikit-learn-python.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][1][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][1][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][2][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][2][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][2][1], methods=['GET', 'POST'])
def Our_Method_and_where_we_will_be_getting_our_Data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/data-acquisition-machine-learning.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][2][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][2][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][3][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][3][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][3][1], methods=['GET', 'POST'])
def Parsing_data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/getting-data-machine-learning.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][3][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][3][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][4][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][4][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][4][1], methods=['GET', 'POST'])
def More_Parsing():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/parsing-data-website-machine-learning.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][4][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][4][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][5][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][5][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][5][1], methods=['GET', 'POST'])
def Structuring_data_with_Pandas():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/using-pandas-structure-process-data.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][5][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][5][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][6][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][6][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][6][1], methods=['GET', 'POST'])
def Getting_more_data_and_meshing_data_sets():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/getting-data-sp-500-index-value-comparison.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][6][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][6][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][7][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][7][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][7][1], methods=['GET', 'POST'])
def Labeling_of_data_part_1():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/labeling-data-machine-learning.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][7][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][7][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][8][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][8][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][8][1], methods=['GET', 'POST'])
def Labeling_data_part_2():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/labeling-data-machine-learning-part-2.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][8][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][8][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][9][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][9][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][9][1], methods=['GET', 'POST'])
def Finally_finishing_up_the_labeling():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/label-data-machine-learning.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][9][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][9][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][10][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][10][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][10][1], methods=['GET', 'POST'])
def Linear_SVC_Machine_learning_SVM_example_with_Python():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/linear-svc-example-scikit-learn-svm-python.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][10][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][10][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][11][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][11][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][11][1], methods=['GET', 'POST'])
def Getting_more_features_from_our_data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/collecting-features-machine-learning.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][11][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][11][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][12][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][12][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][12][1], methods=['GET', 'POST'])
def Linear_SVC_machine_learning_and_testing_our_data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/linear-svc-machine-learning-testing-data.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][12][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][12][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][13][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][13][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][13][1], methods=['GET', 'POST'])
def Scaling_Normalizing_and_machine_learning_with_many_features():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/preprocessing-machine-learning.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][13][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][13][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][14][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][14][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][14][1], methods=['GET', 'POST'])
def Shuffling_our_data_to_solve_a_learning_issue():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/shuffling-data-learning.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][14][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][14][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][15][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][15][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][15][1], methods=['GET', 'POST'])
def Using_Quandl_for_more_data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/using-quandl-data.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][15][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][15][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][16][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][16][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][16][1], methods=['GET', 'POST'])
def Improving_our_Analysis_with_a_more_accurate_measure_of_performance_in_relation_to_fundamentals():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/improving-analysis-machine-learning.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][16][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][16][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][17][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][17][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][17][1], methods=['GET', 'POST'])
def Learning_and_Testing_our_Machine_learning_algorithm():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/learning-and-testing-svm.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][17][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][17][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][18][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][18][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][18][1], methods=['GET', 'POST'])
def More_testing_this_time_including_NA_data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/machine-learning-testing-with-na.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][18][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][18][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][19][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][19][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][19][1], methods=['GET', 'POST'])
def Back_testing_the_strategy():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/back-testing-machine-learning-investing-strategy.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][19][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][19][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][20][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][20][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][20][1], methods=['GET', 'POST'])
def Pulling_current_data_from_Yahoo():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/current-yahoo-data-for-machine-learning.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][20][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][20][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][21][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][21][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][21][1], methods=['GET', 'POST'])
def Building_our_New_Data_set():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/building-yahoo-data-machine-learning.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][21][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][21][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][22][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][22][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][22][1], methods=['GET', 'POST'])
def Searching_for_investment_suggestions():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/investment-suggestions-machine-learning.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][22][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][22][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][23][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][23][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][23][1], methods=['GET', 'POST'])
def Raising_investment_requirement_standards():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/raising-investment-suggestion-requirements.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][23][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][23][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][24][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][24][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][24][1], methods=['GET', 'POST'])
def Testing_raised_standards():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/machine-learning-testing-new-algo.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][24][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][24][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][25][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][25][0])




@app.route(TOPIC_DICT["Support Vector Machines (SVM)"][25][1], methods=['GET', 'POST'])
def Streamlining_the_changing_of_standards():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/streamlining-changing-machine-learning.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][25][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][25][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")



# JUST THE DOWNLOADS PAGE!! 
@app.route("/downloads/intraQuarter.zip/", methods=['GET', 'POST'])
def downloadpage():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Support Vector Machines (SVM)/downloadpage.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Support Vector Machines (SVM)"][0][1], curTitle=TOPIC_DICT["Support Vector Machines (SVM)"][0][0],  nextLink = TOPIC_DICT["Support Vector Machines (SVM)"][1][1], nextTitle = TOPIC_DICT["Support Vector Machines (SVM)"][1][0])






### END SUPPORT VECTOR MACHINE TUTORIALS ###


### BEGIN FOREX ALGO HFT TUTORIALS ###
@app.route(TOPIC_DICT["Forex Algo HFT"][0][1], methods=['GET', 'POST'])
def Introduction():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Forex Algo HFT/machine-learning-pattern-recognition-algorithmic-forex-stock-trading.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][0][1], curTitle=TOPIC_DICT["Forex Algo HFT"][0][0],  nextLink = TOPIC_DICT["Forex Algo HFT"][1][1], nextTitle = TOPIC_DICT["Forex Algo HFT"][1][0])




@app.route(TOPIC_DICT["Forex Algo HFT"][1][1], methods=['GET', 'POST'])
def Quick_Look_at_our_Data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Forex Algo HFT/pattern-recognition-dataset.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][1][1], curTitle=TOPIC_DICT["Forex Algo HFT"][1][0],  nextLink = TOPIC_DICT["Forex Algo HFT"][2][1], nextTitle = TOPIC_DICT["Forex Algo HFT"][2][0])




@app.route(TOPIC_DICT["Forex Algo HFT"][2][1], methods=['GET', 'POST'])
def Basics():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Forex Algo HFT/forex-algo-pattern-rec-basics.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][2][1], curTitle=TOPIC_DICT["Forex Algo HFT"][2][0],  nextLink = TOPIC_DICT["Forex Algo HFT"][3][1], nextTitle = TOPIC_DICT["Forex Algo HFT"][3][0])




@app.route(TOPIC_DICT["Forex Algo HFT"][3][1], methods=['GET', 'POST'])
def Percent_Change():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Forex Algo HFT/percent-change-python.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][3][1], curTitle=TOPIC_DICT["Forex Algo HFT"][3][0],  nextLink = TOPIC_DICT["Forex Algo HFT"][4][1], nextTitle = TOPIC_DICT["Forex Algo HFT"][4][0])




@app.route(TOPIC_DICT["Forex Algo HFT"][4][1], methods=['GET', 'POST'])
def Finding_Patterns():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Forex Algo HFT/finding-forex-algo-patterns.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][4][1], curTitle=TOPIC_DICT["Forex Algo HFT"][4][0],  nextLink = TOPIC_DICT["Forex Algo HFT"][5][1], nextTitle = TOPIC_DICT["Forex Algo HFT"][5][0])




@app.route(TOPIC_DICT["Forex Algo HFT"][5][1], methods=['GET', 'POST'])
def Storing_Patterns():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Forex Algo HFT/storing-found-patterns.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][5][1], curTitle=TOPIC_DICT["Forex Algo HFT"][5][0],  nextLink = TOPIC_DICT["Forex Algo HFT"][6][1], nextTitle = TOPIC_DICT["Forex Algo HFT"][6][0])




@app.route(TOPIC_DICT["Forex Algo HFT"][6][1], methods=['GET', 'POST'])
def Current_Pattern():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Forex Algo HFT/recognizing-current-pattern.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][6][1], curTitle=TOPIC_DICT["Forex Algo HFT"][6][0],  nextLink = TOPIC_DICT["Forex Algo HFT"][7][1], nextTitle = TOPIC_DICT["Forex Algo HFT"][7][0])




@app.route(TOPIC_DICT["Forex Algo HFT"][7][1], methods=['GET', 'POST'])
def Predicting_outcomes():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Forex Algo HFT/predicting-outcomes-of-patterns.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][7][1], curTitle=TOPIC_DICT["Forex Algo HFT"][7][0],  nextLink = TOPIC_DICT["Forex Algo HFT"][8][1], nextTitle = TOPIC_DICT["Forex Algo HFT"][8][0])



@app.route("/average-outcomes-as-predictions-p2/", methods=['GET', 'POST'])
@app.route(TOPIC_DICT["Forex Algo HFT"][8][1], methods=['GET', 'POST'])
def More_predicting():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Forex Algo HFT/more-predicting-outcomes.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][8][1], curTitle=TOPIC_DICT["Forex Algo HFT"][8][0],  nextLink = TOPIC_DICT["Forex Algo HFT"][9][1], nextTitle = TOPIC_DICT["Forex Algo HFT"][9][0])




@app.route(TOPIC_DICT["Forex Algo HFT"][9][1], methods=['GET', 'POST'])
def Increasing_pattern_complexity():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Forex Algo HFT/increasing-pattern-complexity.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][9][1], curTitle=TOPIC_DICT["Forex Algo HFT"][9][0],  nextLink = TOPIC_DICT["Forex Algo HFT"][10][1], nextTitle = TOPIC_DICT["Forex Algo HFT"][10][0])




@app.route(TOPIC_DICT["Forex Algo HFT"][10][1], methods=['GET', 'POST'])
def More_on_Patterns():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Forex Algo HFT/more-on-patterns-hft-forex.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][10][1], curTitle=TOPIC_DICT["Forex Algo HFT"][10][0],  nextLink = TOPIC_DICT["Forex Algo HFT"][11][1], nextTitle = TOPIC_DICT["Forex Algo HFT"][11][0])




@app.route(TOPIC_DICT["Forex Algo HFT"][11][1], methods=['GET', 'POST'])
def Displaying_all_patterns():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Forex Algo HFT/displaying-our-forex-patterns.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][11][1], curTitle=TOPIC_DICT["Forex Algo HFT"][11][0],  nextLink = TOPIC_DICT["Forex Algo HFT"][12][1], nextTitle = TOPIC_DICT["Forex Algo HFT"][12][0])




@app.route(TOPIC_DICT["Forex Algo HFT"][12][1], methods=['GET', 'POST'])
def Variables_in_patterns():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Forex Algo HFT/variables-in-forex-patterns.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][12][1], curTitle=TOPIC_DICT["Forex Algo HFT"][12][0],  nextLink = TOPIC_DICT["Forex Algo HFT"][13][1], nextTitle = TOPIC_DICT["Forex Algo HFT"][13][0])




@app.route(TOPIC_DICT["Forex Algo HFT"][13][1], methods=['GET', 'POST'])
def Past_outcomes_as_possible_predictions():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Forex Algo HFT/past-pattern-outcomes-predictions.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][13][1], curTitle=TOPIC_DICT["Forex Algo HFT"][13][0],  nextLink = TOPIC_DICT["Forex Algo HFT"][14][1], nextTitle = TOPIC_DICT["Forex Algo HFT"][14][0])




@app.route(TOPIC_DICT["Forex Algo HFT"][14][1], methods=['GET', 'POST'])
def Predicting_from_patterns():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Forex Algo HFT/predicting-from-patterns.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][14][1], curTitle=TOPIC_DICT["Forex Algo HFT"][14][0],  nextLink = TOPIC_DICT["Forex Algo HFT"][15][1], nextTitle = TOPIC_DICT["Forex Algo HFT"][15][0])



@app.route(TOPIC_DICT["Forex Algo HFT"][15][1], methods=['GET', 'POST'])
def Average_outcomes_as_predictions():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Forex Algo HFT/average-outcomes-as-predictions-forex-hft.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][15][1], curTitle=TOPIC_DICT["Forex Algo HFT"][15][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")



##
##@app.route(TOPIC_DICT["Forex Algo HFT"][16][1], methods=['GET', 'POST'])
##def Average_outcomes_as_predictions_part_2():
##    update_user_tracking()
##    completed_percentages = topic_completion_percent()
##    return render_template("tutorials/Forex Algo HFT/average-outcomes-as-predictions-p2.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][16][1], curTitle=TOPIC_DICT["Forex Algo HFT"][16][0],  nextLink = TOPIC_DICT["Forex Algo HFT"][17][1], nextTitle = TOPIC_DICT["Forex Algo HFT"][17][0])
##
##
##
##
##@app.route(TOPIC_DICT["Forex Algo HFT"][17][1], methods=['GET', 'POST'])
##def Preparing_back_test():
##    update_user_tracking()
##    completed_percentages = topic_completion_percent()
##    return render_template("tutorials/Forex Algo HFT/preparing-our-backtest-forex-pattern-recognition.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][17][1], curTitle=TOPIC_DICT["Forex Algo HFT"][17][0],  nextLink = TOPIC_DICT["Forex Algo HFT"][18][1], nextTitle = TOPIC_DICT["Forex Algo HFT"][18][0])
##
##
##
##
##@app.route(TOPIC_DICT["Forex Algo HFT"][18][1], methods=['GET', 'POST'])
##def Conclusion_forex():
##    update_user_tracking()
##    completed_percentages = topic_completion_percent()
##    return render_template("tutorials/Forex Algo HFT/forex-algo-hft-python-conclusion.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Forex Algo HFT"][18][1], curTitle=TOPIC_DICT["Forex Algo HFT"][18][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")
### END FOREX ALGO HFT TUTORIALS ###


### BEGIN ROBOTICS PI TUTORIALS ###


@app.route("/raspberry-pi/", methods=['GET', 'POST'])
@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][0][1], methods=['GET', 'POST'])
def Robotics_with_the_Raspberry_Pi():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/robot-remote-control-car-with-the-raspberry-pi.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][0][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][0][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][1][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][1][0])




@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][1][1], methods=['GET', 'POST'])
def Programming_GPIO_example():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/gpio-example-raspberry-pi.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][1][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][1][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][2][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][2][0])





@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][2][1], methods=['GET', 'POST'])
def Running_GPIO():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/running-gpio-python-raspberry-pi.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][2][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][2][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][3][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][3][0])





@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][3][1], methods=['GET', 'POST'])
def Building_Autonomous_RC_car_intro():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/gpio-raspberry-pi-car-intro.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][3][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][3][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][4][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][4][0])




@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][4][1], methods=['GET', 'POST'])
def Supplies_needed():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/raspberry-pi-car-supplies.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][4][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][4][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][5][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][5][0])




@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][5][1], methods=['GET', 'POST'])
def Motor_Control():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/gpio-motor-control-raspberry-pi.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][5][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][5][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][6][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][6][0])




@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][6][1], methods=['GET', 'POST'])
def Connecting_the_four_motors():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/connecting-motors-raspberry-pi.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][6][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][6][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][7][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][7][0])




@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][7][1], methods=['GET', 'POST'])
def Forward_and_Reverse():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/forward-reverse-motors-raspberry-pi.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][7][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][7][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][8][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][8][0])




@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][8][1], methods=['GET', 'POST'])
def Turning():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/turning-raspberry-pi-car.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][8][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][8][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][9][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][9][0])




@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][9][1], methods=['GET', 'POST'])
def Pivoting():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/pivoting-raspberry-pi-car.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][9][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][9][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][10][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][10][0])




@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][10][1], methods=['GET', 'POST'])
def User_Control():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/user-control-raspberry-pi-car.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][10][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][10][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][11][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][11][0])




@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][11][1], methods=['GET', 'POST'])
def Remotely_controlling_the_car():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/raspberry-pi-car-remote-control.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][11][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][11][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][12][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][12][0])




@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][12][1], methods=['GET', 'POST'])
def Adding_a_distance_sensor_HC_SR04():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/raspberry-pi-car-distance-sensor.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][12][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][12][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][13][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][13][0])




@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][13][1], methods=['GET', 'POST'])
def Programming_with_the_distance_sensor():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/raspberry-pi-hc-sr04-programming.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][13][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][13][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][14][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][14][0])




@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][14][1], methods=['GET', 'POST'])
def Autopilot_andor_auto_correct():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/autopilot-raspberry-pi-car.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][14][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][14][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][15][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][15][0])




@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][15][1], methods=['GET', 'POST'])
def Autonomous_Beginnings():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/autonomous-raspberry-pi-car.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][15][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][15][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][16][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][16][0])




@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][16][1], methods=['GET', 'POST'])
def Testing_Autonomous_Code():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/testing-autonomous-raspberry-pi-car.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][16][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][16][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][17][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][17][0])




@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][17][1], methods=['GET', 'POST'])
def Streaming_video_example_one():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/streaming-video-from-raspberry-pi-camera.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][17][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][17][0],  nextLink = TOPIC_DICT["Robotics with the Raspberry Pi"][18][1], nextTitle = TOPIC_DICT["Robotics with the Raspberry Pi"][18][0])




@app.route(TOPIC_DICT["Robotics with the Raspberry Pi"][18][1], methods=['GET', 'POST'])
def Less_latency_streaming_option():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Robotics  with Raspberry Pi/low-latency-video-streaming-raspberry-pi.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Robotics with the Raspberry Pi"][18][1], curTitle=TOPIC_DICT["Robotics with the Raspberry Pi"][18][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")
### END ROBOTICS PI TUTORIALS ###


### BEGIN PYGAME TUTORIALS ###


@app.route("/pygame-making-games-python/", methods=['GET', 'POST'])
@app.route(TOPIC_DICT["PyGame"][0][1], methods=['GET', 'POST'])
def Introduction_to_PyGame():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/pygame-python-3-part-1-intro.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][0][1], curTitle=TOPIC_DICT["PyGame"][0][0],  nextLink = TOPIC_DICT["PyGame"][1][1], nextTitle = TOPIC_DICT["PyGame"][1][0])

@app.route("/pygame-python-3-tutorial-series/", methods=['GET', 'POST'])
def Introduction_to_PyGame2():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/pygame-python-3-part-1-intro.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][0][1], curTitle=TOPIC_DICT["PyGame"][0][0],  nextLink = TOPIC_DICT["PyGame"][1][1], nextTitle = TOPIC_DICT["PyGame"][1][0])




@app.route(TOPIC_DICT["PyGame"][1][1], methods=['GET', 'POST'])
def Displaying_images_with_PyGame():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/displaying-images-pygame.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][1][1], curTitle=TOPIC_DICT["PyGame"][1][0],  nextLink = TOPIC_DICT["PyGame"][2][1], nextTitle = TOPIC_DICT["PyGame"][2][0])




@app.route(TOPIC_DICT["PyGame"][2][1], methods=['GET', 'POST'])
def Moving_an_image_around_in_PyGame():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/pygame-tutorial-moving-images-key-input.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][2][1], curTitle=TOPIC_DICT["PyGame"][2][0],  nextLink = TOPIC_DICT["PyGame"][3][1], nextTitle = TOPIC_DICT["PyGame"][3][0])




@app.route(TOPIC_DICT["PyGame"][3][1], methods=['GET', 'POST'])
def Adding_boundaries():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/adding-boundaries-pygame-video-game.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][3][1], curTitle=TOPIC_DICT["PyGame"][3][0],  nextLink = TOPIC_DICT["PyGame"][4][1], nextTitle = TOPIC_DICT["PyGame"][4][0])




@app.route(TOPIC_DICT["PyGame"][4][1], methods=['GET', 'POST'])
def Displaying_text_to_PyGame_screen():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/displaying-text-pygame-screen.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][4][1], curTitle=TOPIC_DICT["PyGame"][4][0],  nextLink = TOPIC_DICT["PyGame"][5][1], nextTitle = TOPIC_DICT["PyGame"][5][0])




@app.route(TOPIC_DICT["PyGame"][5][1], methods=['GET', 'POST'])
def Drawing_objects_with_PyGame():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/drawing-objects-pygame-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][5][1], curTitle=TOPIC_DICT["PyGame"][5][0],  nextLink = TOPIC_DICT["PyGame"][6][1], nextTitle = TOPIC_DICT["PyGame"][6][0])




@app.route(TOPIC_DICT["PyGame"][6][1], methods=['GET', 'POST'])
def Crashing():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/pygame-crashing-objects.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][6][1], curTitle=TOPIC_DICT["PyGame"][6][0],  nextLink = TOPIC_DICT["PyGame"][7][1], nextTitle = TOPIC_DICT["PyGame"][7][0])




@app.route(TOPIC_DICT["PyGame"][7][1], methods=['GET', 'POST'])
def PyGame_Score():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/adding-score-pygame-video-game.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][7][1], curTitle=TOPIC_DICT["PyGame"][7][0],  nextLink = TOPIC_DICT["PyGame"][8][1], nextTitle = TOPIC_DICT["PyGame"][8][0])




@app.route(TOPIC_DICT["PyGame"][8][1], methods=['GET', 'POST'])
def Drawing_Objects_and_Shapes_in_PyGame():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/pygame-drawing-shapes-objects.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][8][1], curTitle=TOPIC_DICT["PyGame"][8][0],  nextLink = TOPIC_DICT["PyGame"][9][1], nextTitle = TOPIC_DICT["PyGame"][9][0])




@app.route(TOPIC_DICT["PyGame"][9][1], methods=['GET', 'POST'])
def Creating_a_start_menu():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/pygame-start-menu-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][9][1], curTitle=TOPIC_DICT["PyGame"][9][0],  nextLink = TOPIC_DICT["PyGame"][10][1], nextTitle = TOPIC_DICT["PyGame"][10][0])




@app.route(TOPIC_DICT["PyGame"][10][1], methods=['GET', 'POST'])
def PyGame_Buttons_part_1_drawing_the_rectangle():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/pygame-buttons-part-1-button-rectangle.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][10][1], curTitle=TOPIC_DICT["PyGame"][10][0],  nextLink = TOPIC_DICT["PyGame"][11][1], nextTitle = TOPIC_DICT["PyGame"][11][0])




@app.route(TOPIC_DICT["PyGame"][11][1], methods=['GET', 'POST'])
def PyGame_Buttons_part_2_making_the_buttons_interactive():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/making-interactive-pygame-buttons.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][11][1], curTitle=TOPIC_DICT["PyGame"][11][0],  nextLink = TOPIC_DICT["PyGame"][12][1], nextTitle = TOPIC_DICT["PyGame"][12][0])




@app.route(TOPIC_DICT["PyGame"][12][1], methods=['GET', 'POST'])
def PyGame_Buttons_part_3_adding_text_to_the_button():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/placing-text-pygame-buttons.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][12][1], curTitle=TOPIC_DICT["PyGame"][12][0],  nextLink = TOPIC_DICT["PyGame"][13][1], nextTitle = TOPIC_DICT["PyGame"][13][0])




@app.route(TOPIC_DICT["PyGame"][13][1], methods=['GET', 'POST'])
def PyGame_Buttons_part_4_creating_a_general_PyGame_button_function():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/pygame-button-function.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][13][1], curTitle=TOPIC_DICT["PyGame"][13][0],  nextLink = TOPIC_DICT["PyGame"][14][1], nextTitle = TOPIC_DICT["PyGame"][14][0])




@app.route(TOPIC_DICT["PyGame"][14][1], methods=['GET', 'POST'])
def PyGame_Buttons_part_5_running_functions_on_a_button_click():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/pygame-button-function-events.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][14][1], curTitle=TOPIC_DICT["PyGame"][14][0],  nextLink = TOPIC_DICT["PyGame"][15][1], nextTitle = TOPIC_DICT["PyGame"][15][0])




@app.route(TOPIC_DICT["PyGame"][15][1], methods=['GET', 'POST'])
def Converting_PyGame_to_an_executable():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/converting-pygame-executable-cx_freeze.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][15][1], curTitle=TOPIC_DICT["PyGame"][15][0],  nextLink = TOPIC_DICT["PyGame"][16][1], nextTitle = TOPIC_DICT["PyGame"][16][0])




@app.route(TOPIC_DICT["PyGame"][16][1], methods=['GET', 'POST'])
def Adding_a_pause_function_to_our_game_and_Game_Over():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/pause-game-pygame.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][16][1], curTitle=TOPIC_DICT["PyGame"][16][0],  nextLink = TOPIC_DICT["PyGame"][17][1], nextTitle = TOPIC_DICT["PyGame"][17][0])




@app.route(TOPIC_DICT["PyGame"][17][1], methods=['GET', 'POST'])
def PyGame_Icon():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/changing-pygame-icon.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][17][1], curTitle=TOPIC_DICT["PyGame"][17][0],  nextLink = TOPIC_DICT["PyGame"][18][1], nextTitle = TOPIC_DICT["PyGame"][18][0])




@app.route(TOPIC_DICT["PyGame"][18][1], methods=['GET', 'POST'])
def Sounds_and_Music_with_PyGame():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyGame/adding-sounds-music-pygame.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyGame"][18][1], curTitle=TOPIC_DICT["PyGame"][18][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")

### BEGIN PYGAME TUTORIALS ###



#### BEGIN FLASK TUTORIALS ####

@app.route('/web-development-python/', methods=['GET', 'POST'])
@app.route('/flask-web-development-tutorial/', methods=['GET', 'POST'])
@app.route(TOPIC_DICT["Flask"][0][1], methods=['GET', 'POST'])
def Intro_and_environment_creation():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Flask/flask-web-development-introduction.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Flask"][0][1], curTitle=TOPIC_DICT["Flask"][0][0],  nextLink = TOPIC_DICT["Flask"][1][1], nextTitle = TOPIC_DICT["Flask"][1][0])




@app.route(TOPIC_DICT["Flask"][1][1], methods=['GET', 'POST'])
def Basics_initpy_and_your_first_Flask_App():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Flask/creating-first-flask-web-app.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Flask"][1][1], curTitle=TOPIC_DICT["Flask"][1][0],  nextLink = TOPIC_DICT["Flask"][2][1], nextTitle = TOPIC_DICT["Flask"][2][0])




@app.route(TOPIC_DICT["Flask"][2][1], methods=['GET', 'POST'])
def Incorporating_Variables_and_some_Logic():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Flask/templates-flask-variables-html.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Flask"][2][1], curTitle=TOPIC_DICT["Flask"][2][0],  nextLink = TOPIC_DICT["Flask"][3][1], nextTitle = TOPIC_DICT["Flask"][3][0])




@app.route(TOPIC_DICT["Flask"][3][1], methods=['GET', 'POST'])
def Using_Bootstrap_to_make_things_pretty():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Flask/flask-bootstrap.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Flask"][3][1], curTitle=TOPIC_DICT["Flask"][3][0],  nextLink = TOPIC_DICT["Flask"][4][1], nextTitle = TOPIC_DICT["Flask"][4][0])




@app.route(TOPIC_DICT["Flask"][4][1], methods=['GET', 'POST'])
def Using_javascript_plugins_with_a_Highcharts_example():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Flask/adding-js-plugins-flask-highcharts-example.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Flask"][4][1], curTitle=TOPIC_DICT["Flask"][4][0],  nextLink = TOPIC_DICT["Flask"][5][1], nextTitle = TOPIC_DICT["Flask"][5][0])




@app.route(TOPIC_DICT["Flask"][5][1], methods=['GET', 'POST'])
def Incorporating_extends_for_templates():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Flask/flask-template-extends.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Flask"][5][1], curTitle=TOPIC_DICT["Flask"][5][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")

#### END FLASK TUTORIALS ####



#### BEGIN IMAGE RECOGNITION TUTORIALS ####

#/image-recognition

@app.route("/image-recognition/", methods=['GET', 'POST'])
@app.route(TOPIC_DICT["Image Recognition"][0][1], methods=['GET', 'POST'])
def Introduction_and_Dependencies():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Image Recognition/image-recognition-python.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Image Recognition"][0][1], curTitle=TOPIC_DICT["Image Recognition"][0][0],  nextLink = TOPIC_DICT["Image Recognition"][1][1], nextTitle = TOPIC_DICT["Image Recognition"][1][0])




@app.route(TOPIC_DICT["Image Recognition"][1][1], methods=['GET', 'POST'])
def Understanding_Pixel_Arrays():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Image Recognition/python-pixel-arrays.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Image Recognition"][1][1], curTitle=TOPIC_DICT["Image Recognition"][1][0],  nextLink = TOPIC_DICT["Image Recognition"][2][1], nextTitle = TOPIC_DICT["Image Recognition"][2][0])




@app.route(TOPIC_DICT["Image Recognition"][2][1], methods=['GET', 'POST'])
def More_Pixel_Arrays():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Image Recognition/more-pixel-arrays.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Image Recognition"][2][1], curTitle=TOPIC_DICT["Image Recognition"][2][0],  nextLink = TOPIC_DICT["Image Recognition"][3][1], nextTitle = TOPIC_DICT["Image Recognition"][3][0])




@app.route(TOPIC_DICT["Image Recognition"][3][1], methods=['GET', 'POST'])
def Graphing_our_images_in_Matplotlib():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Image Recognition/graphing-images-matplotlib.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Image Recognition"][3][1], curTitle=TOPIC_DICT["Image Recognition"][3][0],  nextLink = TOPIC_DICT["Image Recognition"][4][1], nextTitle = TOPIC_DICT["Image Recognition"][4][0])




@app.route(TOPIC_DICT["Image Recognition"][4][1], methods=['GET', 'POST'])
def Thresholding():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Image Recognition/image-thresholding-python.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Image Recognition"][4][1], curTitle=TOPIC_DICT["Image Recognition"][4][0],  nextLink = TOPIC_DICT["Image Recognition"][5][1], nextTitle = TOPIC_DICT["Image Recognition"][5][0])




@app.route(TOPIC_DICT["Image Recognition"][5][1], methods=['GET', 'POST'])
def Thresholding_Function():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Image Recognition/thresholding-python-function.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Image Recognition"][5][1], curTitle=TOPIC_DICT["Image Recognition"][5][0],  nextLink = TOPIC_DICT["Image Recognition"][6][1], nextTitle = TOPIC_DICT["Image Recognition"][6][0])




@app.route(TOPIC_DICT["Image Recognition"][6][1], methods=['GET', 'POST'])
def Thresholding_Logic():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Image Recognition/automated-image-thresholding-python.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Image Recognition"][6][1], curTitle=TOPIC_DICT["Image Recognition"][6][0],  nextLink = TOPIC_DICT["Image Recognition"][7][1], nextTitle = TOPIC_DICT["Image Recognition"][7][0])




@app.route(TOPIC_DICT["Image Recognition"][7][1], methods=['GET', 'POST'])
def Saving_our_Data_For_Training_and_Testing():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Image Recognition/saving-image-data.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Image Recognition"][7][1], curTitle=TOPIC_DICT["Image Recognition"][7][0],  nextLink = TOPIC_DICT["Image Recognition"][8][1], nextTitle = TOPIC_DICT["Image Recognition"][8][0])




@app.route(TOPIC_DICT["Image Recognition"][8][1], methods=['GET', 'POST'])
def Basic_Testing():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Image Recognition/basic-image-recognition-testing.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Image Recognition"][8][1], curTitle=TOPIC_DICT["Image Recognition"][8][0],  nextLink = TOPIC_DICT["Image Recognition"][9][1], nextTitle = TOPIC_DICT["Image Recognition"][9][0])



@app.route(TOPIC_DICT["Image Recognition"][9][1], methods=['GET', 'POST'])
def Testing_visualization_and_moving_forward():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Image Recognition/testing-visualization-and-conclusion.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Image Recognition"][9][1], curTitle=TOPIC_DICT["Image Recognition"][9][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")
#### END IMAGE RECOGNITION TUTORIALS ####


#### BEGIN PYQT TUTORIALS ####
@app.route(TOPIC_DICT["PyQt"][0][1], methods=['GET', 'POST'])
def PyQt_Tutorials_coming_soon():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyQt/pyqt-python-programming-tutorials.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyQt"][0][1], curTitle=TOPIC_DICT["PyQt"][0][0],  nextLink = TOPIC_DICT["PyQt"][1][1], nextTitle = TOPIC_DICT["PyQt"][1][0])
#### END PYQT TUTORIALS ####




#### BEGIN DJANGO TUTORIALS ####
@app.route(TOPIC_DICT["Django"][0][1], methods=['GET', 'POST'])
def Django_Development_Videos():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Django/python-web-development-django.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Django"][0][1], curTitle=TOPIC_DICT["Django"][0][0],  nextLink = "/dashboard/", nextTitle = "Dashboard")
#### END DJANGO TUTORIALS ####




#### BEGIN PYOPENGL TUTORIALS ####

@app.route(TOPIC_DICT["PyOpenGL"][0][1], methods=['GET', 'POST'])
def OpenGL_with_PyOpenGL_introduction_and_creation_of_Rotating_Cube():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyOpenGL/opengl-rotating-cube-example-pyopengl-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyOpenGL"][0][1], curTitle=TOPIC_DICT["PyOpenGL"][0][0],  nextLink = TOPIC_DICT["PyOpenGL"][1][1], nextTitle = TOPIC_DICT["PyOpenGL"][1][0])

@app.route('/opengl-pyopengl-python-pygame-tutorial/', methods=['GET', 'POST'])
def OpenGL_with_PyOpenGL_introduction_and_creation_of_Rotating_Cube2():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyOpenGL/opengl-rotating-cube-example-pyopengl-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyOpenGL"][0][1], curTitle=TOPIC_DICT["PyOpenGL"][0][0],  nextLink = TOPIC_DICT["PyOpenGL"][1][1], nextTitle = TOPIC_DICT["PyOpenGL"][1][0])




@app.route(TOPIC_DICT["PyOpenGL"][1][1], methods=['GET', 'POST'])
def Coloring_Surfaces_as_well_as_understand_some_of_the_basic_OpenGL_code():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyOpenGL/coloring-pyopengl-surfaces-python-opengl.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyOpenGL"][1][1], curTitle=TOPIC_DICT["PyOpenGL"][1][0],  nextLink = TOPIC_DICT["PyOpenGL"][2][1], nextTitle = TOPIC_DICT["PyOpenGL"][2][0])




@app.route(TOPIC_DICT["PyOpenGL"][2][1], methods=['GET', 'POST'])
def Understanding_navigation_within_the_3D_environment_via_OpenGL():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyOpenGL/navigating-3d-environment.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyOpenGL"][2][1], curTitle=TOPIC_DICT["PyOpenGL"][2][0],  nextLink = TOPIC_DICT["PyOpenGL"][3][1], nextTitle = TOPIC_DICT["PyOpenGL"][3][0])




@app.route(TOPIC_DICT["PyOpenGL"][3][1], methods=['GET', 'POST'])
def Moving_the_player_automatically_towards_the_cube():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyOpenGL/moving-towards-pyopengl-cube.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyOpenGL"][3][1], curTitle=TOPIC_DICT["PyOpenGL"][3][0],  nextLink = TOPIC_DICT["PyOpenGL"][4][1], nextTitle = TOPIC_DICT["PyOpenGL"][4][0])




@app.route(TOPIC_DICT["PyOpenGL"][4][1], methods=['GET', 'POST'])
def Random_Cube_Position():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyOpenGL/random-cube-position-pyopengl-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyOpenGL"][4][1], curTitle=TOPIC_DICT["PyOpenGL"][4][0],  nextLink = TOPIC_DICT["PyOpenGL"][5][1], nextTitle = TOPIC_DICT["PyOpenGL"][5][0])




@app.route(TOPIC_DICT["PyOpenGL"][5][1], methods=['GET', 'POST'])
def Adding_Many_Cubes_to_our_Game():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyOpenGL/multiple-opengl-cubes.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyOpenGL"][5][1], curTitle=TOPIC_DICT["PyOpenGL"][5][0],  nextLink = TOPIC_DICT["PyOpenGL"][6][1], nextTitle = TOPIC_DICT["PyOpenGL"][6][0])




@app.route(TOPIC_DICT["PyOpenGL"][6][1], methods=['GET', 'POST'])
def Adding_a_ground_in_OpenGL():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyOpenGL/adding-ground-pyopengl-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyOpenGL"][6][1], curTitle=TOPIC_DICT["PyOpenGL"][6][0],  nextLink = TOPIC_DICT["PyOpenGL"][7][1], nextTitle = TOPIC_DICT["PyOpenGL"][7][0])




@app.route(TOPIC_DICT["PyOpenGL"][7][1], methods=['GET', 'POST'])
def Infinite_flying_cubes():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyOpenGL/infinite-3d-pyopengl-flying-cubes-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyOpenGL"][7][1], curTitle=TOPIC_DICT["PyOpenGL"][7][0],  nextLink = TOPIC_DICT["PyOpenGL"][8][1], nextTitle = TOPIC_DICT["PyOpenGL"][8][0])




@app.route(TOPIC_DICT["PyOpenGL"][8][1], methods=['GET', 'POST'])
def Optimizing_the_processing_for_infinite_cubes():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/PyOpenGL/improving-infinite-3d-cubes-pyopengl-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["PyOpenGL"][8][1], curTitle=TOPIC_DICT["PyOpenGL"][8][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")

#### END PYOPENGL TUTORIALS ####




#### BEGIN DATA MANIPULATION TUTORIALS ####
# /python-pandas-data-analysis/


@app.route('/python-2-7-pandas-data-analysis/', methods=['GET', 'POST'])
@app.route('/data-analysis/', methods=['GET', 'POST'])
@app.route('/python-pandas-data-analysis/', methods=['GET', 'POST'])
@app.route(TOPIC_DICT["Data Manipulation"][0][1], methods=['GET', 'POST'])
def Saving_to_a_CSV_and_reading_from_a_CSV_with_Pandas():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Manipulation/pandas-saving-reading-csv-file.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Manipulation"][0][1], curTitle=TOPIC_DICT["Data Manipulation"][0][0],  nextLink = TOPIC_DICT["Data Manipulation"][1][1], nextTitle = TOPIC_DICT["Data Manipulation"][1][0])




@app.route(TOPIC_DICT["Data Manipulation"][1][1], methods=['GET', 'POST'])
def Column_manipulation():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Manipulation/pandas-column-manipulation-spreadsheet-data.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Manipulation"][1][1], curTitle=TOPIC_DICT["Data Manipulation"][1][0],  nextLink = TOPIC_DICT["Data Manipulation"][2][1], nextTitle = TOPIC_DICT["Data Manipulation"][2][0])




@app.route(TOPIC_DICT["Data Manipulation"][2][1], methods=['GET', 'POST'])
def Column_Operations_basic_math_operations_and_moving_averages():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Manipulation/pandas-column-operations-calculations.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Manipulation"][2][1], curTitle=TOPIC_DICT["Data Manipulation"][2][0],  nextLink = TOPIC_DICT["Data Manipulation"][3][1], nextTitle = TOPIC_DICT["Data Manipulation"][3][0])


@app.route("/graphing-pandas-matplotlib/", methods=['GET', 'POST'])
@app.route(TOPIC_DICT["Data Manipulation"][3][1], methods=['GET', 'POST'])
def threeD_Visualization_of2():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Manipulation/2D Visualization of Pandas data with Matplotlib, including plotting dates.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Manipulation"][3][1], curTitle=TOPIC_DICT["Data Manipulation"][3][0],  nextLink = TOPIC_DICT["Data Manipulation"][4][1], nextTitle = TOPIC_DICT["Data Manipulation"][4][0])




@app.route(TOPIC_DICT["Data Manipulation"][4][1], methods=['GET', 'POST'])
def threeD_Visualization_of():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Manipulation/3d-graphing-pandas-matplotlib.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Manipulation"][4][1], curTitle=TOPIC_DICT["Data Manipulation"][4][0],  nextLink = TOPIC_DICT["Data Manipulation"][5][1], nextTitle = TOPIC_DICT["Data Manipulation"][5][0])




@app.route(TOPIC_DICT["Data Manipulation"][5][1], methods=['GET', 'POST'])
def Standard_Deviation_datamanip():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Manipulation/pandas-standard-deviation.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Manipulation"][5][1], curTitle=TOPIC_DICT["Data Manipulation"][5][0],  nextLink = TOPIC_DICT["Data Manipulation"][6][1], nextTitle = TOPIC_DICT["Data Manipulation"][6][0])




@app.route(TOPIC_DICT["Data Manipulation"][6][1], methods=['GET', 'POST'])
def Correlation_matrix_and_Statistics_Information_on_Data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Manipulation/pandas-statistics-correlation-tables-how-to.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Manipulation"][6][1], curTitle=TOPIC_DICT["Data Manipulation"][6][0],  nextLink = TOPIC_DICT["Data Manipulation"][7][1], nextTitle = TOPIC_DICT["Data Manipulation"][7][0])




@app.route(TOPIC_DICT["Data Manipulation"][7][1], methods=['GET', 'POST'])
def Function_mapping_for_advanced_Pandas_users():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Manipulation/python-function-mapping-pandas.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Manipulation"][7][1], curTitle=TOPIC_DICT["Data Manipulation"][7][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")

#### END DATA MANIPULATION TUTORIALS ####




#### BEGIN DATA VISUALIZATION TUTORIALS ####
#@app.route("/matplotlib-graphing-series/", methods=['GET', 'POST'])
@app.route(TOPIC_DICT["Data Visualization"][0][1], methods=['GET', 'POST'])
def Matplotlib_Crash_Course_dataviz():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Visualization/matplotlib-python-3-basics-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Visualization"][0][1], curTitle=TOPIC_DICT["Data Visualization"][0][0],  nextLink = TOPIC_DICT["Data Visualization"][1][1], nextTitle = TOPIC_DICT["Data Visualization"][1][0])




@app.route(TOPIC_DICT["Data Visualization"][1][1], methods=['GET', 'POST'])
def threeD_graphs_in_Matplotlib():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Visualization/3d-graphing-python-matplotlib.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Visualization"][1][1], curTitle=TOPIC_DICT["Data Visualization"][1][0],  nextLink = TOPIC_DICT["Data Visualization"][2][1], nextTitle = TOPIC_DICT["Data Visualization"][2][0])




@app.route(TOPIC_DICT["Data Visualization"][2][1], methods=['GET', 'POST'])
def threeD_Scatter_Plot_with_Python_and_Matplotlib():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Visualization/matplotlib-3d-scatterplot-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Visualization"][2][1], curTitle=TOPIC_DICT["Data Visualization"][2][0],  nextLink = TOPIC_DICT["Data Visualization"][3][1], nextTitle = TOPIC_DICT["Data Visualization"][3][0])




@app.route(TOPIC_DICT["Data Visualization"][3][1], methods=['GET', 'POST'])
def More_3D_scatter_plotting_with_custom_colors():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Visualization/3d-scatter-plot-customizing.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Visualization"][3][1], curTitle=TOPIC_DICT["Data Visualization"][3][0],  nextLink = TOPIC_DICT["Data Visualization"][4][1], nextTitle = TOPIC_DICT["Data Visualization"][4][0])




@app.route(TOPIC_DICT["Data Visualization"][4][1], methods=['GET', 'POST'])
def threeD_Barcharts():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Visualization/3d-bar-charts-python-matplotlib.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Visualization"][4][1], curTitle=TOPIC_DICT["Data Visualization"][4][0],  nextLink = TOPIC_DICT["Data Visualization"][5][1], nextTitle = TOPIC_DICT["Data Visualization"][5][0])




@app.route(TOPIC_DICT["Data Visualization"][5][1], methods=['GET', 'POST'])
def threeD_Plane_wireframe_Graph():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Visualization/wireframe-graph-python.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Visualization"][5][1], curTitle=TOPIC_DICT["Data Visualization"][5][0],  nextLink = TOPIC_DICT["Data Visualization"][6][1], nextTitle = TOPIC_DICT["Data Visualization"][6][0])




@app.route(TOPIC_DICT["Data Visualization"][6][1], methods=['GET', 'POST'])
def Live_Updating_Graphs_with_Matplotlib_Tutorial():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Visualization/python-matplotlib-live-updating-graphs.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Visualization"][6][1], curTitle=TOPIC_DICT["Data Visualization"][6][0],  nextLink = TOPIC_DICT["Data Visualization"][7][1], nextTitle = TOPIC_DICT["Data Visualization"][7][0])




@app.route(TOPIC_DICT["Data Visualization"][7][1], methods=['GET', 'POST'])
def Modify_Data_Granularity_for_Graphing_Data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Visualization/modifying-data-granularity-matplotlib.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Visualization"][7][1], curTitle=TOPIC_DICT["Data Visualization"][7][0],  nextLink = TOPIC_DICT["Data Visualization"][8][1], nextTitle = TOPIC_DICT["Data Visualization"][8][0])




@app.route(TOPIC_DICT["Data Visualization"][8][1], methods=['GET', 'POST'])
def Geographical_Plotting_with_Basemap_and_Python_p1():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Visualization/geographical-plotting-basemap-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Visualization"][8][1], curTitle=TOPIC_DICT["Data Visualization"][8][0],  nextLink = TOPIC_DICT["Data Visualization"][9][1], nextTitle = TOPIC_DICT["Data Visualization"][9][0])




@app.route(TOPIC_DICT["Data Visualization"][9][1], methods=['GET', 'POST'])
def Geographical_Plotting_with_Basemap_and_Python_p2():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Visualization/map-plotting-basemap-matplotlib-part-2.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Visualization"][9][1], curTitle=TOPIC_DICT["Data Visualization"][9][0],  nextLink = TOPIC_DICT["Data Visualization"][10][1], nextTitle = TOPIC_DICT["Data Visualization"][10][0])




@app.route(TOPIC_DICT["Data Visualization"][10][1], methods=['GET', 'POST'])
def Geographical_Plotting_with_Basemap_and_Python_p3():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Visualization/basemap-possibilities.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Visualization"][10][1], curTitle=TOPIC_DICT["Data Visualization"][10][0],  nextLink = TOPIC_DICT["Data Visualization"][11][1], nextTitle = TOPIC_DICT["Data Visualization"][11][0])




@app.route("/basemap-python-plotting-tutorial-part-4/", methods=['GET', 'POST'])
@app.route(TOPIC_DICT["Data Visualization"][11][1], methods=['GET', 'POST'])
def Geographical_Plotting_with_Basemap_and_Python_p4():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Visualization/plotting-maps-python-basemap.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Visualization"][11][1], curTitle=TOPIC_DICT["Data Visualization"][11][0],  nextLink = TOPIC_DICT["Data Visualization"][12][1], nextTitle = TOPIC_DICT["Data Visualization"][12][0])




@app.route(TOPIC_DICT["Data Visualization"][12][1], methods=['GET', 'POST'])
def Geographical_Plotting_with_Basemap_and_Python_p5():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Visualization/basemap-python-plotting-tutorial-part-5.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Visualization"][12][1], curTitle=TOPIC_DICT["Data Visualization"][12][0],  nextLink = TOPIC_DICT["Data Visualization"][13][1], nextTitle = TOPIC_DICT["Data Visualization"][13][0])




@app.route(TOPIC_DICT["Data Visualization"][13][1], methods=['GET', 'POST'])
def Advanced_Matplotlib_Series_videos_and_ending_source_only():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Data Visualization/advanced-matplotlib-graphing-charting-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Data Visualization"][13][1], curTitle=TOPIC_DICT["Data Visualization"][13][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")
#### END DATA VISUALIZATION TUTORIALS ####


#### BEGIN KIVY TUTORIALS ####
@app.route(TOPIC_DICT["Kivy"][0][1], methods=['GET', 'POST'])
def Kivy_with_Python_tutorial_for_Mobile_Application_Development_Part_1():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Kivy/kivy-application-development-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Kivy"][0][1], curTitle=TOPIC_DICT["Kivy"][0][0],  nextLink = TOPIC_DICT["Kivy"][1][1], nextTitle = TOPIC_DICT["Kivy"][1][0])




@app.route(TOPIC_DICT["Kivy"][1][1], methods=['GET', 'POST'])
def Kivy_Widgets_and_Labels():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Kivy/kivy-widgets-labels.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Kivy"][1][1], curTitle=TOPIC_DICT["Kivy"][1][0],  nextLink = TOPIC_DICT["Kivy"][2][1], nextTitle = TOPIC_DICT["Kivy"][2][0])




@app.route(TOPIC_DICT["Kivy"][2][1], methods=['GET', 'POST'])
def The_Kivy_kv_Language():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Kivy/kivy-language-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Kivy"][2][1], curTitle=TOPIC_DICT["Kivy"][2][0],  nextLink = TOPIC_DICT["Kivy"][3][1], nextTitle = TOPIC_DICT["Kivy"][3][0])




@app.route(TOPIC_DICT["Kivy"][3][1], methods=['GET', 'POST'])
def Kivy_kv_Language_contd():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Kivy/more-kivy-language.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Kivy"][3][1], curTitle=TOPIC_DICT["Kivy"][3][0],  nextLink = TOPIC_DICT["Kivy"][4][1], nextTitle = TOPIC_DICT["Kivy"][4][0])




@app.route(TOPIC_DICT["Kivy"][4][1], methods=['GET', 'POST'])
def Dynamic_Resizable_Placement():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Kivy/dynamic-kivy-content-placement.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Kivy"][4][1], curTitle=TOPIC_DICT["Kivy"][4][0],  nextLink = TOPIC_DICT["Kivy"][5][1], nextTitle = TOPIC_DICT["Kivy"][5][0])




@app.route(TOPIC_DICT["Kivy"][5][1], methods=['GET', 'POST'])
def Layouts_Float_Layout():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Kivy/kivy-float-layout.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Kivy"][5][1], curTitle=TOPIC_DICT["Kivy"][5][0],  nextLink = TOPIC_DICT["Kivy"][6][1], nextTitle = TOPIC_DICT["Kivy"][6][0])




@app.route(TOPIC_DICT["Kivy"][6][1], methods=['GET', 'POST'])
def Getting_Mouse__Press__Touch_Input():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Kivy/getting-mouse-press-touch-input-kivy.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Kivy"][6][1], curTitle=TOPIC_DICT["Kivy"][6][0],  nextLink = TOPIC_DICT["Kivy"][7][1], nextTitle = TOPIC_DICT["Kivy"][7][0])




@app.route(TOPIC_DICT["Kivy"][7][1], methods=['GET', 'POST'])
def Simple_Drawing_Application():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Kivy/kivy-drawing-application-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Kivy"][7][1], curTitle=TOPIC_DICT["Kivy"][7][0],  nextLink = TOPIC_DICT["Kivy"][8][1], nextTitle = TOPIC_DICT["Kivy"][8][0])




@app.route(TOPIC_DICT["Kivy"][8][1], methods=['GET', 'POST'])
def Builder_for_loading_kv_Files_Smarter():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Kivy/kivy-loader-for-style.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Kivy"][8][1], curTitle=TOPIC_DICT["Kivy"][8][0],  nextLink = TOPIC_DICT["Kivy"][9][1], nextTitle = TOPIC_DICT["Kivy"][9][0])




@app.route(TOPIC_DICT["Kivy"][9][1], methods=['GET', 'POST'])
def Screen_Manager_for_Multiple_Screens():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Kivy/kivy-screen-manager-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Kivy"][9][1], curTitle=TOPIC_DICT["Kivy"][9][0],  nextLink = TOPIC_DICT["Kivy"][10][1], nextTitle = TOPIC_DICT["Kivy"][10][0])




@app.route(TOPIC_DICT["Kivy"][10][1], methods=['GET', 'POST'])
def Drawing_Application_with_Screen_Manager():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Kivy/drawing-application-with-screen-manager.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Kivy"][10][1], curTitle=TOPIC_DICT["Kivy"][10][0],  nextLink = TOPIC_DICT["Kivy"][11][1], nextTitle = TOPIC_DICT["Kivy"][11][0])




@app.route(TOPIC_DICT["Kivy"][11][1], methods=['GET', 'POST'])
def Adding_better_Navigation():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Kivy/kivy-application-navigation.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Kivy"][11][1], curTitle=TOPIC_DICT["Kivy"][11][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")
#### END KIVY TUTORIALS ####



#### BEGIN TKINTER TUTORIALS ####
@app.route(TOPIC_DICT["Tkinter"][0][1], methods=['GET', 'POST'])
def Programming_GUIs_and_windows_with_Tkinter_and_Python_Introduction_():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/tkinter-depth-tutorial-making-actual-program.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][0][1], curTitle=TOPIC_DICT["Tkinter"][0][0],  nextLink = TOPIC_DICT["Tkinter"][1][1], nextTitle = TOPIC_DICT["Tkinter"][1][0])




@app.route(TOPIC_DICT["Tkinter"][1][1], methods=['GET', 'POST'])
def Object_Oriented_Programming_Crash_Course_with_Tkinter():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/object-oriented-programming-crash-course-tkinter.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][1][1], curTitle=TOPIC_DICT["Tkinter"][1][0],  nextLink = TOPIC_DICT["Tkinter"][2][1], nextTitle = TOPIC_DICT["Tkinter"][2][0])




@app.route(TOPIC_DICT["Tkinter"][2][1], methods=['GET', 'POST'])
def Passing_functions_with_Parameters_in_Tkinter_using_Lambda():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/passing-functions-parameters-tkinter-using-lambda.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][2][1], curTitle=TOPIC_DICT["Tkinter"][2][0],  nextLink = TOPIC_DICT["Tkinter"][3][1], nextTitle = TOPIC_DICT["Tkinter"][3][0])




@app.route(TOPIC_DICT["Tkinter"][3][1], methods=['GET', 'POST'])
def How_to_change_and_show_a_new_window_in_Tkinter():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/change-show-new-frame-tkinter.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][3][1], curTitle=TOPIC_DICT["Tkinter"][3][0],  nextLink = TOPIC_DICT["Tkinter"][4][1], nextTitle = TOPIC_DICT["Tkinter"][4][0])




@app.route(TOPIC_DICT["Tkinter"][4][1], methods=['GET', 'POST'])
def Styling_your_GUI_a_bit_using_TTK():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/styling-gui-bit-using-ttk.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][4][1], curTitle=TOPIC_DICT["Tkinter"][4][0],  nextLink = TOPIC_DICT["Tkinter"][5][1], nextTitle = TOPIC_DICT["Tkinter"][5][0])



@app.route("/embed-matplotlib-graph-tkinter-gui/", methods=['GET', 'POST'])
@app.route(TOPIC_DICT["Tkinter"][5][1], methods=['GET', 'POST'])
def How_to_embed_a_Matplotlib_graph_to_your_Tkinter_GUI():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/How to embed a Matplotlib graph to your Tkinter GUI.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][5][1], curTitle=TOPIC_DICT["Tkinter"][5][0],  nextLink = TOPIC_DICT["Tkinter"][6][1], nextTitle = TOPIC_DICT["Tkinter"][6][0])




@app.route(TOPIC_DICT["Tkinter"][6][1], methods=['GET', 'POST'])
def How_to_make_the_Matplotlib_graph_live_in_your_application():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/embedding-live-matplotlib-graph-tkinter-gui.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][6][1], curTitle=TOPIC_DICT["Tkinter"][6][0],  nextLink = TOPIC_DICT["Tkinter"][7][1], nextTitle = TOPIC_DICT["Tkinter"][7][0])




@app.route(TOPIC_DICT["Tkinter"][7][1], methods=['GET', 'POST'])
def Organizing_our_GUI():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/organizing-gui.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][7][1], curTitle=TOPIC_DICT["Tkinter"][7][0],  nextLink = TOPIC_DICT["Tkinter"][8][1], nextTitle = TOPIC_DICT["Tkinter"][8][0])




@app.route(TOPIC_DICT["Tkinter"][8][1], methods=['GET', 'POST'])
def Plotting_Live_Updating_Data_in_Matplotlib_and_our_Tkinter_GUI():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/plotting-live-bitcoin-price-data-tkinter-matplotlib.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][8][1], curTitle=TOPIC_DICT["Tkinter"][8][0],  nextLink = TOPIC_DICT["Tkinter"][9][1], nextTitle = TOPIC_DICT["Tkinter"][9][0])




@app.route(TOPIC_DICT["Tkinter"][9][1], methods=['GET', 'POST'])
def Customizing_an_embedded_Matplotlib_Graph_in_Tkinter():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/customizing-tkinter-matplotlib-graph.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][9][1], curTitle=TOPIC_DICT["Tkinter"][9][0],  nextLink = TOPIC_DICT["Tkinter"][10][1], nextTitle = TOPIC_DICT["Tkinter"][10][0])




@app.route(TOPIC_DICT["Tkinter"][10][1], methods=['GET', 'POST'])
def Creating_our_Main_Menu_in_Tkinter():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/creating-main-menu-tkinter.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][10][1], curTitle=TOPIC_DICT["Tkinter"][10][0],  nextLink = TOPIC_DICT["Tkinter"][11][1], nextTitle = TOPIC_DICT["Tkinter"][11][0])




@app.route(TOPIC_DICT["Tkinter"][11][1], methods=['GET', 'POST'])
def Building_a_pop_up_message_window():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/tkinter-popup-message-window.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][11][1], curTitle=TOPIC_DICT["Tkinter"][11][0],  nextLink = TOPIC_DICT["Tkinter"][12][1], nextTitle = TOPIC_DICT["Tkinter"][12][0])




@app.route(TOPIC_DICT["Tkinter"][12][1], methods=['GET', 'POST'])
def Exchange_Choice_Option():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/adding-tkinter-menu-options.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][12][1], curTitle=TOPIC_DICT["Tkinter"][12][0],  nextLink = TOPIC_DICT["Tkinter"][13][1], nextTitle = TOPIC_DICT["Tkinter"][13][0])




@app.route(TOPIC_DICT["Tkinter"][13][1], methods=['GET', 'POST'])
def Time_frame_and_sample_size_option():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/time-frame-sample-size-options.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][13][1], curTitle=TOPIC_DICT["Tkinter"][13][0],  nextLink = TOPIC_DICT["Tkinter"][14][1], nextTitle = TOPIC_DICT["Tkinter"][14][0])




@app.route(TOPIC_DICT["Tkinter"][14][1], methods=['GET', 'POST'])
def Adding_indicator_Menus_3_videos():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/adding-indicator-choice-menu.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][14][1], curTitle=TOPIC_DICT["Tkinter"][14][0],  nextLink = TOPIC_DICT["Tkinter"][15][1], nextTitle = TOPIC_DICT["Tkinter"][15][0])




@app.route(TOPIC_DICT["Tkinter"][15][1], methods=['GET', 'POST'])
def Trading_option_startstop_and_help_menu_options():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/adding-trading-option.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][15][1], curTitle=TOPIC_DICT["Tkinter"][15][0],  nextLink = TOPIC_DICT["Tkinter"][16][1], nextTitle = TOPIC_DICT["Tkinter"][16][0])




@app.route(TOPIC_DICT["Tkinter"][16][1], methods=['GET', 'POST'])
def Tutorial_on_adding_a_tutorial():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/tutorial-for-tkinter-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][16][1], curTitle=TOPIC_DICT["Tkinter"][16][0],  nextLink = TOPIC_DICT["Tkinter"][17][1], nextTitle = TOPIC_DICT["Tkinter"][17][0])




@app.route(TOPIC_DICT["Tkinter"][17][1], methods=['GET', 'POST'])
def Allowing_the_exchange_choice_option_to_affect_actual_shown_exchange():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/exchange-choice-handling.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][17][1], curTitle=TOPIC_DICT["Tkinter"][17][0],  nextLink = TOPIC_DICT["Tkinter"][18][1], nextTitle = TOPIC_DICT["Tkinter"][18][0])




@app.route(TOPIC_DICT["Tkinter"][18][1], methods=['GET', 'POST'])
def Adding_exchange_choice_contd():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/adding-exchanges-2.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][18][1], curTitle=TOPIC_DICT["Tkinter"][18][0],  nextLink = TOPIC_DICT["Tkinter"][19][1], nextTitle = TOPIC_DICT["Tkinter"][19][0])




@app.route(TOPIC_DICT["Tkinter"][19][1], methods=['GET', 'POST'])
def Adding_exchange_choices_part_3():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/adding-exchanges-3.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][19][1], curTitle=TOPIC_DICT["Tkinter"][19][0],  nextLink = TOPIC_DICT["Tkinter"][20][1], nextTitle = TOPIC_DICT["Tkinter"][20][0])




@app.route(TOPIC_DICT["Tkinter"][20][1], methods=['GET', 'POST'])
def Indicator_Support():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/adding-indicator-support.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][20][1], curTitle=TOPIC_DICT["Tkinter"][20][0],  nextLink = TOPIC_DICT["Tkinter"][21][1], nextTitle = TOPIC_DICT["Tkinter"][21][0])




@app.route(TOPIC_DICT["Tkinter"][21][1], methods=['GET', 'POST'])
def Pulling_data_from_the_Sea_of_BTC_API():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/pulling-data-from-seaofbtc.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][21][1], curTitle=TOPIC_DICT["Tkinter"][21][0],  nextLink = TOPIC_DICT["Tkinter"][22][1], nextTitle = TOPIC_DICT["Tkinter"][22][0])




@app.route(TOPIC_DICT["Tkinter"][22][1], methods=['GET', 'POST'])
def Setting_up_sub_plots_within_our_Tkinter_GUI():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/subplots-within-tkinter-gui.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][22][1], curTitle=TOPIC_DICT["Tkinter"][22][0],  nextLink = TOPIC_DICT["Tkinter"][23][1], nextTitle = TOPIC_DICT["Tkinter"][23][0])




@app.route(TOPIC_DICT["Tkinter"][23][1], methods=['GET', 'POST'])
def Graphing_an_OHLC_candlestick_graph_embedded_in_our_Tkinter_GUI():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/graphing-ohlc-candlestick-in-tkinter.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][23][1], curTitle=TOPIC_DICT["Tkinter"][23][0],  nextLink = TOPIC_DICT["Tkinter"][24][1], nextTitle = TOPIC_DICT["Tkinter"][24][0])




@app.route(TOPIC_DICT["Tkinter"][24][1], methods=['GET', 'POST'])
def Acquiring_RSI_data_from_Sea_of_BTC_API():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/getting-rsi-data-for-tkinter-gui.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][24][1], curTitle=TOPIC_DICT["Tkinter"][24][0],  nextLink = TOPIC_DICT["Tkinter"][25][1], nextTitle = TOPIC_DICT["Tkinter"][25][0])




@app.route(TOPIC_DICT["Tkinter"][25][1], methods=['GET', 'POST'])
def Acquiring_MACD_data_from_Sea_of_BTC_API():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/getting-macd-data-for-tkinter-gui.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][25][1], curTitle=TOPIC_DICT["Tkinter"][25][0],  nextLink = TOPIC_DICT["Tkinter"][26][1], nextTitle = TOPIC_DICT["Tkinter"][26][0])




@app.route(TOPIC_DICT["Tkinter"][26][1], methods=['GET', 'POST'])
def Converting_Tkinter_application_to_exe_and_installer_with_cx_Freeze():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Tkinter/converting-tkinter-to-exe-with-cx-freeze.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Tkinter"][26][1], curTitle=TOPIC_DICT["Tkinter"][26][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")
#### END TKINTER TUTORIALS ####


#### BEGIN CLUSTERING UNSUPERVISED LEARNING TUTORIALS ####
@app.route(TOPIC_DICT["Clustering (unsupervised learning)"][0][1], methods=['GET', 'POST'])
def Unsupervised_Machine_Learning_Flat_Clustering():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Clustering (unsupervised learning)/flat-clustering-machine-learning-python-scikit-learn.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Clustering (unsupervised learning)"][0][1], curTitle=TOPIC_DICT["Clustering (unsupervised learning)"][0][0],  nextLink = TOPIC_DICT["Clustering (unsupervised learning)"][1][1], nextTitle = TOPIC_DICT["Clustering (unsupervised learning)"][1][0])




@app.route(TOPIC_DICT["Clustering (unsupervised learning)"][1][1], methods=['GET', 'POST'])
def Unsupervised_Machine_Learning_hierarchical_Clustering():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Clustering (unsupervised learning)/hierarchical-clustering-machine-learning-python-scikit-learn.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Clustering (unsupervised learning)"][1][1], curTitle=TOPIC_DICT["Clustering (unsupervised learning)"][1][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")

#### END CLUSTERING UNSUPERVISED LEARNING TUTORIALS ####





##### BEGIN NLTK #####


@app.route("/sentiment-analysis-natural-language-processing/", methods=['GET', 'POST'])
@app.route(TOPIC_DICT["Natural Language Processing with NLTK"][0][1], methods=['GET', 'POST'])
def Simple_RSS_feed_scraping():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Natural Language Processing with NLTK/scraping-parsing-rss-feed.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Natural Language Processing with NLTK"][0][1], curTitle=TOPIC_DICT["Natural Language Processing with NLTK"][0][0],  nextLink = TOPIC_DICT["Natural Language Processing with NLTK"][1][1], nextTitle = TOPIC_DICT["Natural Language Processing with NLTK"][1][0])




@app.route(TOPIC_DICT["Natural Language Processing with NLTK"][1][1], methods=['GET', 'POST'])
def Simple_website_scraping():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Natural Language Processing with NLTK/scraping-text-websites.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Natural Language Processing with NLTK"][1][1], curTitle=TOPIC_DICT["Natural Language Processing with NLTK"][1][0],  nextLink = TOPIC_DICT["Natural Language Processing with NLTK"][2][1], nextTitle = TOPIC_DICT["Natural Language Processing with NLTK"][2][0])




@app.route(TOPIC_DICT["Natural Language Processing with NLTK"][2][1], methods=['GET', 'POST'])
def More_ParsingScraping():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Natural Language Processing with NLTK/website-scraping-basics.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Natural Language Processing with NLTK"][2][1], curTitle=TOPIC_DICT["Natural Language Processing with NLTK"][2][0],  nextLink = TOPIC_DICT["Natural Language Processing with NLTK"][3][1], nextTitle = TOPIC_DICT["Natural Language Processing with NLTK"][3][0])




@app.route(TOPIC_DICT["Natural Language Processing with NLTK"][3][1], methods=['GET', 'POST'])
def Installing_the_Natural_Language_Toolkit_NLTK():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Natural Language Processing with NLTK/installing-nltk-nlp-python.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Natural Language Processing with NLTK"][3][1], curTitle=TOPIC_DICT["Natural Language Processing with NLTK"][3][0],  nextLink = TOPIC_DICT["Natural Language Processing with NLTK"][4][1], nextTitle = TOPIC_DICT["Natural Language Processing with NLTK"][4][0])




@app.route(TOPIC_DICT["Natural Language Processing with NLTK"][4][1], methods=['GET', 'POST'])
def NLTK_Part_of_Speech_Tagging_Tutorial():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Natural Language Processing with NLTK/natural-language-toolkit-nltk-part-speech-tagging.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Natural Language Processing with NLTK"][4][1], curTitle=TOPIC_DICT["Natural Language Processing with NLTK"][4][0],  nextLink = TOPIC_DICT["Natural Language Processing with NLTK"][5][1], nextTitle = TOPIC_DICT["Natural Language Processing with NLTK"][5][0])




@app.route(TOPIC_DICT["Natural Language Processing with NLTK"][5][1], methods=['GET', 'POST'])
def Named_Entity_Recognition_NLTK_tutorial():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Natural Language Processing with NLTK/named-entity-recognition-nltk-python.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Natural Language Processing with NLTK"][5][1], curTitle=TOPIC_DICT["Natural Language Processing with NLTK"][5][0],  nextLink = TOPIC_DICT["Natural Language Processing with NLTK"][6][1], nextTitle = TOPIC_DICT["Natural Language Processing with NLTK"][6][0])




@app.route(TOPIC_DICT["Natural Language Processing with NLTK"][6][1], methods=['GET', 'POST'])
def Building_a_Knowledge_base():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Natural Language Processing with NLTK/building-nlp-knowledge-base.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Natural Language Processing with NLTK"][6][1], curTitle=TOPIC_DICT["Natural Language Processing with NLTK"][6][0],  nextLink = TOPIC_DICT["Natural Language Processing with NLTK"][7][1], nextTitle = TOPIC_DICT["Natural Language Processing with NLTK"][7][0])




@app.route(TOPIC_DICT["Natural Language Processing with NLTK"][7][1], methods=['GET', 'POST'])
def More_Named_Entity_Recognition_with_NLTK():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Natural Language Processing with NLTK/more-named-entity-recognition.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Natural Language Processing with NLTK"][7][1], curTitle=TOPIC_DICT["Natural Language Processing with NLTK"][7][0],  nextLink = TOPIC_DICT["Natural Language Processing with NLTK"][8][1], nextTitle = TOPIC_DICT["Natural Language Processing with NLTK"][8][0])




@app.route(TOPIC_DICT["Natural Language Processing with NLTK"][8][1], methods=['GET', 'POST'])
def Pulling_related_Sentiment_about_Named_Entities():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Natural Language Processing with NLTK/finding-related-sentiment.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Natural Language Processing with NLTK"][8][1], curTitle=TOPIC_DICT["Natural Language Processing with NLTK"][8][0],  nextLink = TOPIC_DICT["Natural Language Processing with NLTK"][9][1], nextTitle = TOPIC_DICT["Natural Language Processing with NLTK"][9][0])




@app.route(TOPIC_DICT["Natural Language Processing with NLTK"][9][1], methods=['GET', 'POST'])
def Populating_a_knowledge_base():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Natural Language Processing with NLTK/populating-nlp-database.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Natural Language Processing with NLTK"][9][1], curTitle=TOPIC_DICT["Natural Language Processing with NLTK"][9][0],  nextLink = TOPIC_DICT["Natural Language Processing with NLTK"][10][1], nextTitle = TOPIC_DICT["Natural Language Processing with NLTK"][10][0])




@app.route(TOPIC_DICT["Natural Language Processing with NLTK"][10][1], methods=['GET', 'POST'])
def What_next():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Natural Language Processing with NLTK/what-next-nlp-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Natural Language Processing with NLTK"][10][1], curTitle=TOPIC_DICT["Natural Language Processing with NLTK"][10][0],  nextLink = TOPIC_DICT["Natural Language Processing with NLTK"][11][1], nextTitle = TOPIC_DICT["Natural Language Processing with NLTK"][11][0])




@app.route(TOPIC_DICT["Natural Language Processing with NLTK"][11][1], methods=['GET', 'POST'])
def Accuracy_Testing():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Natural Language Processing with NLTK/accuracy-testing-basic-nlp.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Natural Language Processing with NLTK"][11][1], curTitle=TOPIC_DICT["Natural Language Processing with NLTK"][11][0],  nextLink = TOPIC_DICT["Natural Language Processing with NLTK"][12][1], nextTitle = TOPIC_DICT["Natural Language Processing with NLTK"][12][0])




@app.route(TOPIC_DICT["Natural Language Processing with NLTK"][12][1], methods=['GET', 'POST'])
def Building_back_testing():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Natural Language Processing with NLTK/back-testing-nlp-nltk.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Natural Language Processing with NLTK"][12][1], curTitle=TOPIC_DICT["Natural Language Processing with NLTK"][12][0],  nextLink = TOPIC_DICT["Natural Language Processing with NLTK"][13][1], nextTitle = TOPIC_DICT["Natural Language Processing with NLTK"][13][0])




@app.route(TOPIC_DICT["Natural Language Processing with NLTK"][13][1], methods=['GET', 'POST'])
def Machine_learning_and_Sentiment_Analysis():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Natural Language Processing with NLTK/learning-for-sentiment-analysis.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Natural Language Processing with NLTK"][13][1], curTitle=TOPIC_DICT["Natural Language Processing with NLTK"][13][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")
##### END NLTK #####



##### BEGIN IBPY #####

@app.route(TOPIC_DICT["IBpy"][0][1], methods=['GET', 'POST'])
def IBPy_Tutorial_for_using_Interactive_Brokers_API_with_Python():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/IBpy/ibpy-tutorial-using-interactive-brokers-api-python.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["IBpy"][0][1], curTitle=TOPIC_DICT["IBpy"][0][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")
##### END IBPY #####


##### BEGIN FUNDAMENTAL INVESTING #####


@app.route(TOPIC_DICT["Programming for Fundamental Investing"][0][1], methods=['GET', 'POST'])
def Programming_for_Fundamental_Investing():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/python-fundamental-investing.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][0][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][0][0],  nextLink = TOPIC_DICT["Programming for Fundamental Investing"][1][1], nextTitle = TOPIC_DICT["Programming for Fundamental Investing"][1][0])




@app.route(TOPIC_DICT["Programming for Fundamental Investing"][1][1], methods=['GET', 'POST'])
def Getting_Company_Data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/fundamental-company-data.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][1][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][1][0],  nextLink = TOPIC_DICT["Programming for Fundamental Investing"][2][1], nextTitle = TOPIC_DICT["Programming for Fundamental Investing"][2][0])




@app.route(TOPIC_DICT["Programming for Fundamental Investing"][2][1], methods=['GET', 'POST'])
def Price_to_Book_ratio_example():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/price-to-book-ratio.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][2][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][2][0],  nextLink = TOPIC_DICT["Programming for Fundamental Investing"][3][1], nextTitle = TOPIC_DICT["Programming for Fundamental Investing"][3][0])




@app.route(TOPIC_DICT["Programming for Fundamental Investing"][3][1], methods=['GET', 'POST'])
def Python_Stock_Screener_for_Price_to_Book():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/create-a-stock-screener-python.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][3][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][3][0],  nextLink = TOPIC_DICT["Programming for Fundamental Investing"][4][1], nextTitle = TOPIC_DICT["Programming for Fundamental Investing"][4][0])




@app.route(TOPIC_DICT["Programming for Fundamental Investing"][4][1], methods=['GET', 'POST'])
def Python_Screener_for_PEG_Ratio():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/peg-ratio-stock-screener.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][4][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][4][0],  nextLink = TOPIC_DICT["Programming for Fundamental Investing"][5][1], nextTitle = TOPIC_DICT["Programming for Fundamental Investing"][5][0])




@app.route(TOPIC_DICT["Programming for Fundamental Investing"][5][1], methods=['GET', 'POST'])
def Adding_Price_to_Earnings():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/price-to-earnings-screener.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][5][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][5][0],  nextLink = TOPIC_DICT["Programming for Fundamental Investing"][6][1], nextTitle = TOPIC_DICT["Programming for Fundamental Investing"][6][0])




@app.route(TOPIC_DICT["Programming for Fundamental Investing"][6][1], methods=['GET', 'POST'])
def Getting_all_Russell_3000_stock_tickers():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/compiling-russell-3000-tickers.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][6][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][6][0],  nextLink = TOPIC_DICT["Programming for Fundamental Investing"][7][1], nextTitle = TOPIC_DICT["Programming for Fundamental Investing"][7][0])




@app.route(TOPIC_DICT["Programming for Fundamental Investing"][7][1], methods=['GET', 'POST'])
def Getting_all_Russell_3000_stock_tickers_part_2():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/compiling-russell-3000-tickers-2.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][7][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][7][0],  nextLink = TOPIC_DICT["Programming for Fundamental Investing"][8][1], nextTitle = TOPIC_DICT["Programming for Fundamental Investing"][8][0])




@app.route(TOPIC_DICT["Programming for Fundamental Investing"][8][1], methods=['GET', 'POST'])
def More_stock_Screening():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/more-stock-screening.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][8][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][8][0],  nextLink = TOPIC_DICT["Programming for Fundamental Investing"][9][1], nextTitle = TOPIC_DICT["Programming for Fundamental Investing"][9][0])




@app.route(TOPIC_DICT["Programming for Fundamental Investing"][9][1], methods=['GET', 'POST'])
def Completing_Basic_Stock_Screener():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/completing-basic-stock-screener.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][9][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][9][0],  nextLink = TOPIC_DICT["Programming for Fundamental Investing"][10][1], nextTitle = TOPIC_DICT["Programming for Fundamental Investing"][10][0])




@app.route(TOPIC_DICT["Programming for Fundamental Investing"][10][1], methods=['GET', 'POST'])
def Connecting_with_Quandl_for_Annual_Earnings_Data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/connecting-with-quandl.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][10][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][10][0],  nextLink = TOPIC_DICT["Programming for Fundamental Investing"][11][1], nextTitle = TOPIC_DICT["Programming for Fundamental Investing"][11][0])




@app.route(TOPIC_DICT["Programming for Fundamental Investing"][11][1], methods=['GET', 'POST'])
def Organizing_Earnings_Data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/organizing-earnings-data.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][11][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][11][0],  nextLink = TOPIC_DICT["Programming for Fundamental Investing"][12][1], nextTitle = TOPIC_DICT["Programming for Fundamental Investing"][12][0])




@app.route(TOPIC_DICT["Programming for Fundamental Investing"][12][1], methods=['GET', 'POST'])
def Graphing_Finance_Data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/graphing-finance-data-fundamentals.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][12][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][12][0],  nextLink = TOPIC_DICT["Programming for Fundamental Investing"][13][1], nextTitle = TOPIC_DICT["Programming for Fundamental Investing"][13][0])




@app.route(TOPIC_DICT["Programming for Fundamental Investing"][13][1], methods=['GET', 'POST'])
def Finishing_the_Graphing():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/finishing-fundamental-graphing.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][13][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][13][0],  nextLink = TOPIC_DICT["Programming for Fundamental Investing"][14][1], nextTitle = TOPIC_DICT["Programming for Fundamental Investing"][14][0])




@app.route(TOPIC_DICT["Programming for Fundamental Investing"][14][1], methods=['GET', 'POST'])
def Adding_the_Graphing_to_the_Screener():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/incorporating-graphing-into-stock-screener.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][14][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][14][0],  nextLink = TOPIC_DICT["Programming for Fundamental Investing"][15][1], nextTitle = TOPIC_DICT["Programming for Fundamental Investing"][15][0])




@app.route(TOPIC_DICT["Programming for Fundamental Investing"][15][1], methods=['GET', 'POST'])
def Preparing_figure_to_Accept_Finance_Data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/preparing-figure-for-finance-data.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][15][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][15][0],  nextLink = TOPIC_DICT["Programming for Fundamental Investing"][16][1], nextTitle = TOPIC_DICT["Programming for Fundamental Investing"][16][0])




@app.route(TOPIC_DICT["Programming for Fundamental Investing"][16][1], methods=['GET', 'POST'])
def Adding_Historical_Earnings_to_Stock_Screener_Chart_Data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/adding-historical-earnings.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][16][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][16][0],  nextLink = TOPIC_DICT["Programming for Fundamental Investing"][17][1], nextTitle = TOPIC_DICT["Programming for Fundamental Investing"][17][0])




@app.route(TOPIC_DICT["Programming for Fundamental Investing"][17][1], methods=['GET', 'POST'])
def Completing_the_Fundamental_Investing_Stock_Screeners():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Programming for Fundamental Investing/fundamental-investing-stock-screener-conclusion.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Programming for Fundamental Investing"][17][1], curTitle=TOPIC_DICT["Programming for Fundamental Investing"][17][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")

##### END FUNDAMENTAL INVESTING #####


##### BEGIN SENTIMENT ANALYSIS WITH PANDAS #####


@app.route(TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][0][1], methods=['GET', 'POST'])
def Python_and_Pandas_with_Sentiment_Analysis_Databas():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Python and Pandas with Sentiment Analysis Database/python-and-pandas-for-sentiment-analysis-and-finance.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][0][1], curTitle=TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][0][0],  nextLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][1][1], nextTitle = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][1][0])




@app.route(TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][1][1], methods=['GET', 'POST'])
def Pandas_Basics():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Python and Pandas with Sentiment Analysis Database/pandas-basics-sentiment.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][1][1], curTitle=TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][1][0],  nextLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][2][1], nextTitle = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][2][0])




@app.route(TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][2][1], methods=['GET', 'POST'])
def Looking_at_our_Data():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Python and Pandas with Sentiment Analysis Database/sentiment-analysis-data.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][2][1], curTitle=TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][2][0],  nextLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][3][1], nextTitle = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][3][0])




@app.route(TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][3][1], methods=['GET', 'POST'])
def Data_Manipulation():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Python and Pandas with Sentiment Analysis Database/simple-data-manipulation.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][3][1], curTitle=TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][3][0],  nextLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][4][1], nextTitle = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][4][0])




@app.route(TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][4][1], methods=['GET', 'POST'])
def Removing_Outlier_Plots():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Python and Pandas with Sentiment Analysis Database/removing-outliers-sentiment.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][4][1], curTitle=TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][4][0],  nextLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][5][1], nextTitle = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][5][0])




@app.route(TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][5][1], methods=['GET', 'POST'])
def Basics_for_a_Strategy():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Python and Pandas with Sentiment Analysis Database/simple-strategy-idea.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][5][1], curTitle=TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][5][0],  nextLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][6][1], nextTitle = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][6][0])




@app.route(TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][6][1], methods=['GET', 'POST'])
def Dynamic_Moving_Averages():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Python and Pandas with Sentiment Analysis Database/dynamic-moving-averages.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][6][1], curTitle=TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][6][0],  nextLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][7][1], nextTitle = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][7][0])




@app.route(TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][7][1], methods=['GET', 'POST'])
def Strategy_Function():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Python and Pandas with Sentiment Analysis Database/strategy-function-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][7][1], curTitle=TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][7][0],  nextLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][8][1], nextTitle = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][8][0])




@app.route(TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][8][1], methods=['GET', 'POST'])
def Mapping_function_to_dataframe():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Python and Pandas with Sentiment Analysis Database/mapping-function-pandas-sentiment.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][8][1], curTitle=TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][8][0],  nextLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][9][1], nextTitle = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][9][0])




@app.route(TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][9][1], methods=['GET', 'POST'])
def Beginning_to_back_test():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Python and Pandas with Sentiment Analysis Database/back-testing-basics-sentiment.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][9][1], curTitle=TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][9][0],  nextLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][10][1], nextTitle = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][10][0])




@app.route(TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][10][1], methods=['GET', 'POST'])
def More_Analysis():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Python and Pandas with Sentiment Analysis Database/more-analysis-sentiment.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][10][1], curTitle=TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][10][0],  nextLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][11][1], nextTitle = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][11][0])




@app.route(TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][11][1], methods=['GET', 'POST'])
def Conclusion():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Python and Pandas with Sentiment Analysis Database/sentiment-conclusion.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][11][1], curTitle=TOPIC_DICT["Python and Pandas with Sentiment Analysis Database"][11][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")

##### END SENTIMENT ANALYSIS WITH PANDAS #####


##### BEGIN MONTE CARLO #####


@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][0][1], methods=['GET', 'POST'])
def Monte_Carlo_Introduction():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/monte-carlo-simulator-python.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][0][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][0][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][1][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][1][0])



@app.route("/creating-dice-roll-monte-carlo-simulator/", methods=['GET', 'POST'])
@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][1][1], methods=['GET', 'POST'])
def Monte_Carlo_dice_Function():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/monte-carlo-dice-function.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][1][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][1][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][2][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][2][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][2][1], methods=['GET', 'POST'])
def Creating_a_simple_Bettor():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/simple-bettor.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][2][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][2][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][3][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][3][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][3][1], methods=['GET', 'POST'])
def Plotting_Results_with_Matpltolib():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/plotting-monte-carlo-matplotlib.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][3][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][3][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][4][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][4][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][4][1], methods=['GET', 'POST'])
def Martingale_Strategy():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/martingale-strategy.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][4][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][4][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][5][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][5][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][5][1], methods=['GET', 'POST'])
def Bettor_Statistics():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/bettor-statistics-monte-carlo.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][5][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][5][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][6][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][6][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][6][1], methods=['GET', 'POST'])
def More_comparison():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/more-monte-carlo-comparison.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][6][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][6][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][7][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][7][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][7][1], methods=['GET', 'POST'])
def Graphing_Monte_Carlo():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/graphing-monte-carlo.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][7][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][7][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][8][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][8][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][8][1], methods=['GET', 'POST'])
def Fixing_Debt_Issues():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/fixing-debt-issues-monte-carlo.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][8][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][8][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][9][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][9][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][9][1], methods=['GET', 'POST'])
def Analyzing_Monte_Carlo_results():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/analyzing-monte-carlo-results.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][9][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][9][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][10][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][10][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][10][1], methods=['GET', 'POST'])
def Using_Monte_Carlo_to_find_Best_multiple():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/using-monte-carlo-to-snoop.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][10][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][10][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][11][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][11][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][11][1], methods=['GET', 'POST'])
def Checking_betting_results():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/checking-bettor-results.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][11][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][11][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][12][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][12][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][12][1], methods=['GET', 'POST'])
def DAlembert_Strategy():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/dalembert-strategy.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][12][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][12][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][13][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][13][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][13][1], methods=['GET', 'POST'])
def fiddyfiddy_Odds():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/50-50-odds.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][13][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][13][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][14][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][14][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][14][1], methods=['GET', 'POST'])
def Analysis_of_DAlembert():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/dalembert-analysis.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][14][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][14][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][15][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][15][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][15][1], methods=['GET', 'POST'])
def Comparing_Profitability():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/comparing-profitability.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][15][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][15][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][16][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][16][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][16][1], methods=['GET', 'POST'])
def Finding_best_DAlembert_Multiple():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/snooping-best-dalembert-multiple.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][16][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][16][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][17][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][17][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][17][1], methods=['GET', 'POST'])
def Two_dimensional_charting_monte_carlo():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/two-dimension-graph-monte-carlo.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][17][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][17][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][18][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][18][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][18][1], methods=['GET', 'POST'])
def Monte_Carlo_Simulation_and_Python():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/monte-carlo-python.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][18][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][18][0],  nextLink = TOPIC_DICT["Creating a Monte Carlo simulator"][19][1], nextTitle = TOPIC_DICT["Creating a Monte Carlo simulator"][19][0])




@app.route(TOPIC_DICT["Creating a Monte Carlo simulator"][19][1], methods=['GET', 'POST'])
def Labouchere_System_for_Gambling_Tested():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Creating a Monte Carlo simulator/testing-labouchere.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Creating a Monte Carlo simulator"][19][1], curTitle=TOPIC_DICT["Creating a Monte Carlo simulator"][19][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")
##### END MONTE CARLO #####




#####  BEGIN VPS #####

@app.route(TOPIC_DICT["Virtual Private Server Basics"][0][1], methods=['GET', 'POST'])
def VPS_with_AWS_EC2_and_Python_intro():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Virtual Private Server Basics/python-vps-intro.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Virtual Private Server Basics"][0][1], curTitle=TOPIC_DICT["Virtual Private Server Basics"][0][0],  nextLink = TOPIC_DICT["Virtual Private Server Basics"][1][1], nextTitle = TOPIC_DICT["Virtual Private Server Basics"][1][0])




@app.route(TOPIC_DICT["Virtual Private Server Basics"][1][1], methods=['GET', 'POST'])
def Navigating_the_Terminal():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Virtual Private Server Basics/navigating-terminal.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Virtual Private Server Basics"][1][1], curTitle=TOPIC_DICT["Virtual Private Server Basics"][1][0],  nextLink = TOPIC_DICT["Virtual Private Server Basics"][2][1], nextTitle = TOPIC_DICT["Virtual Private Server Basics"][2][0])




@app.route(TOPIC_DICT["Virtual Private Server Basics"][2][1], methods=['GET', 'POST'])
def Navigating_the_Terminal_p2():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Virtual Private Server Basics/terminal-navigation.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Virtual Private Server Basics"][2][1], curTitle=TOPIC_DICT["Virtual Private Server Basics"][2][0],  nextLink = TOPIC_DICT["Virtual Private Server Basics"][3][1], nextTitle = TOPIC_DICT["Virtual Private Server Basics"][3][0])




@app.route(TOPIC_DICT["Virtual Private Server Basics"][3][1], methods=['GET', 'POST'])
def Crontab_tutorial_for_cron_jobs():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Virtual Private Server Basics/cron-tutorial-vps.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Virtual Private Server Basics"][3][1], curTitle=TOPIC_DICT["Virtual Private Server Basics"][3][0],  nextLink = TOPIC_DICT["Virtual Private Server Basics"][4][1], nextTitle = TOPIC_DICT["Virtual Private Server Basics"][4][0])




@app.route(TOPIC_DICT["Virtual Private Server Basics"][4][1], methods=['GET', 'POST'])
def Running_Multiple_Scripts_at_Once():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Virtual Private Server Basics/running-multiple-scripts.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Virtual Private Server Basics"][4][1], curTitle=TOPIC_DICT["Virtual Private Server Basics"][4][0],  nextLink = TOPIC_DICT["Virtual Private Server Basics"][5][1], nextTitle = TOPIC_DICT["Virtual Private Server Basics"][5][0])




@app.route(TOPIC_DICT["Virtual Private Server Basics"][5][1], methods=['GET', 'POST'])
def Using_nohup_command_to_Keep_Scripts_Alive():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Virtual Private Server Basics/nohup-command.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Virtual Private Server Basics"][5][1], curTitle=TOPIC_DICT["Virtual Private Server Basics"][5][0],  nextLink = TOPIC_DICT["Virtual Private Server Basics"][6][1], nextTitle = TOPIC_DICT["Virtual Private Server Basics"][6][0])




@app.route(TOPIC_DICT["Virtual Private Server Basics"][6][1], methods=['GET', 'POST'])
def Python_Anywhere_using_PythonAnywhere():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Virtual Private Server Basics/python-anywhere.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Virtual Private Server Basics"][6][1], curTitle=TOPIC_DICT["Virtual Private Server Basics"][6][0],  nextLink = '/dashboard/', nextTitle = "Dashboard")
#####  END VPS #####






######## BEGIN PRACTICAL FLASK ########

@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][0][1], methods=['GET', 'POST'])
def Introduction_to_Practical_Flask():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/practical-flask-introduction.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][0][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][0][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][1][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][1][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][1][1], methods=['GET', 'POST'])
def Basic_Flask_Website_tutorial():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/basic-flask-website-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][1][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][1][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][2][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][2][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][2][1], methods=['GET', 'POST'])
def Flask_with_Bootstrap_and_Jinja_Templating():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/bootstrap-jinja-templates-flask.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][2][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][2][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][3][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][3][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][3][1], methods=['GET', 'POST'])
def Starting_our_Website_home_page():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/website-home-page-flask.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][3][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][3][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][4][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][4][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][4][1], methods=['GET', 'POST'])
def Improving_the_Home_Page():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/flask-homepage-improvements.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][4][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][4][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][5][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][5][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][5][1], methods=['GET', 'POST'])
def Finishing_the_Home_Page():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/flask-homepage-completed.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][5][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][5][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][6][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][6][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][6][1], methods=['GET', 'POST'])
def Dynamic_User_Dashboard():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/flask-user-dashboard.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][6][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][6][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][7][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][7][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][7][1], methods=['GET', 'POST'])
def Content_Management_Beginnings():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/flask-content-management-basics.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][7][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][7][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][8][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][8][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][8][1], methods=['GET', 'POST'])
def Error_Handling():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/flask-error-handling-basics.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][8][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][8][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][9][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][9][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][9][1], methods=['GET', 'POST'])
def Flask_Flash_function():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/flash-flask-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][9][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][9][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][10][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][10][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][10][1], methods=['GET', 'POST'])
def Users_with_Flask_intro():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/flask-users-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][10][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][10][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][11][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][11][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][11][1], methods=['GET', 'POST'])
def Handling_POST_and_GET_Requests_with_Flask():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/flask-get-post-requests-handling-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][11][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][11][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][12][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][12][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][12][1], methods=['GET', 'POST'])
def Creating_MySQL_database_and_table():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/mysql-database-with-flask-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][12][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][12][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][13][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][13][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][13][1], methods=['GET', 'POST'])
def Connecting_to_MySQL_database_with_MySQLdb():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/flask-connect-mysql-using-mysqldb-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][13][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][13][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][14][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][14][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][14][1], methods=['GET', 'POST'])
def User_Registration_Form():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/flask-user-registration-form-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][14][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][14][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][15][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][15][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][15][1], methods=['GET', 'POST'])
def Registration_Code():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/flask-registration-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][15][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][15][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][16][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][16][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][16][1], methods=['GET', 'POST'])
def Finishing_User_Registration():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/flask-user-register-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][16][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][16][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][17][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][17][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][17][1], methods=['GET', 'POST'])
def Password_Hashing_with_Flask_Tutorial():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/password-hashing-flask-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][17][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][17][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][18][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][18][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][18][1], methods=['GET', 'POST'])
def User_Login_System():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/flask-user-log-in-system-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][18][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][18][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][19][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][19][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][19][1], methods=['GET', 'POST'])
def Decorators___Login_Required_pages():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/decorator-wrappers-flask-tutorial-login-required.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][19][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][19][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][20][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][20][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][20][1], methods=['GET', 'POST'])
def Dynamic_user_based_content():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/dynamic-user-based-content-flask-tutorial.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][20][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][20][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][21][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][21][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][21][1], methods=['GET', 'POST'])
def More_on_Content_Management():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/flask-content-management-contd.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][21][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][21][0],  nextLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][22][1], nextTitle = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][22][0])




@app.route(TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][22][1], methods=['GET', 'POST'])
def Practical_Flask_Conclusion():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Practical Flask Creating PythonProgrammingnet/flask-conclusion-practical.html",completed_percentages=completed_percentages, curLink = TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][22][1], curTitle=TOPIC_DICT["Practical Flask Creating PythonProgrammingnet"][22][0],  nextLink = "/dashboard/", nextTitle = "Dashboard")



######## END PRACTICAL FLASK ########









#### BEGIN SINGLES #####


@app.route("/plotting-sql-database-python-matplotlib/", methods=['GET', 'POST'])
def plotting_sql_db():
    try:
        update_user_tracking()
        completed_percentages = topic_completion_percent()
        return render_template("tutorials/singles/plotting-sql-database-python-matplotlib.html",completed_percentages=completed_percentages)
    except Exception as e:
        return(str(e))



@app.route("/matplotlib-reading-information-file-plotting/", methods=['GET', 'POST'])
def reading_from_file_plotting():
    try:
        update_user_tracking()
        completed_percentages = topic_completion_percent()
        return render_template("tutorials/singles/matplotlib-reading-information-file-plotting.html",completed_percentages=completed_percentages)
    except Exception as e:
        return(str(e))



@app.route("/graphing-matplotlib-python-part-3-colors-line-thickness/", methods=['GET', 'POST'])
def colors_and_line_thickness():
    try:
        update_user_tracking()
        completed_percentages = topic_completion_percent()
        return render_template("tutorials/singles/graphing-matplotlib-python-part-3-colors-line-thickness.html",completed_percentages=completed_percentages)
    except Exception as e:
        return(str(e))
    


@app.route("/adding-color-graphs-python-matplotlib-tutorial-4/", methods=['GET', 'POST'])
def color_graphs_p_4():
    try:
        update_user_tracking()
        completed_percentages = topic_completion_percent()
        return render_template("tutorials/singles/adding-color-graphs-python-matplotlib-tutorial-4.html",completed_percentages=completed_percentages)
    except Exception as e:
        return(str(e))

@app.route("/matplotlib-tutorial-part-5-subplots-multiple-plots-figure/", methods=['GET', 'POST'])
def subplots_graphs_p_5():
    try:
        update_user_tracking()
        completed_percentages = topic_completion_percent()
        return render_template("tutorials/singles/matplotlib-tutorial-part-5-subplots-multiple-plots-figure.html",completed_percentages=completed_percentages)
    except Exception as e:
        return(str(e))


# JUST THE DOWNLOADS PAGE!! 
@app.route("/downloads/knowledgeBase.db", methods=['GET', 'POST'])
def downloadpage_knowledgebase():
    update_user_tracking()
    completed_percentages = topic_completion_percent()
    return render_template("tutorials/Natural Language Processing with NLTK/downloadpage.html",completed_percentages=completed_percentages)

















if __name__ == "__main__":
    app.run()

    
