##
##//
##
##
##// CURRENT:
##// list of topics by {TOPIC:[["TITLE", "URL"]]}
##
##// FUTURE:
##////list of topics by {TOPIC:[["TITLE", "URL", "TAGS"],
##////                          ["TITLE", "URL", "TAGS"]]}

def Content():
##    //             Suggest Branches for next steps
##    //             If liked: Matplotlib, link to data analysis or Pandas maybe
##    //             If liked: GUI stuff: Kivy, PyGame, Tkinter
##    //             if liked: Text and word-based: NLTK
    TOPIC_DICT = {


                  "Practical Flask: Creating PythonProgramming.net":[["Introduction to Practical Flask","/practical-flask-introduction/"],
                                                                     ["Basic Flask Website tutorial","/basic-flask-website-tutorial/"],
                                                                     ["Flask with Bootstrap and Jinja Templating","/bootstrap-jinja-templates-flask/"],
                                                                     ["Starting our Website home page","/website-home-page-flask/"],
                                                                     ["Improving the Home Page","/flask-homepage-improvements/"],
                                                                     ["Finishing the Home Page","/flask-homepage-completed/"],
                                                                     ["Dynamic User Dashboard","/flask-user-dashboard/"],
                                                                     ["Content Management Beginnings","/flask-content-management-basics/"],
                                                                     ["Error Handling","/flask-error-handling-basics/"],
                                                                     ["Flask Flash function","/flash-flask-tutorial/"],
                                                                     ["Users with Flask intro","/flask-users-tutorial/"],
                                                                     ["Handling POST and GET Requests with Flask","/flask-get-post-requests-handling-tutorial/"],
                                                                     ["Creating MySQL database and table","/mysql-database-with-flask-tutorial/"],
                                                                     ["Connecting to MySQL database with MySQLdb","/flask-connect-mysql-using-mysqldb-tutorial/"],
                                                                     ["User Registration Form","/flask-user-registration-form-tutorial/"],
                                                                     ["Registration Code","/flask-registration-tutorial/"],
                                                                     ["Finishing User Registration","/flask-user-register-tutorial/"],
                                                                     ["Password Hashing with Flask Tutorial","/password-hashing-flask-tutorial/"],
                                                                     ["User Login System","/flask-user-log-in-system-tutorial/"],
                                                                     ["Decorators - Login_Required pages","/decorator-wrappers-flask-tutorial-login-required/"],
                                                                     ["Dynamic user-based content","/dynamic-user-based-content-flask-tutorial/"],
                                                                     ["More on Content Management","/flask-content-management-contd/"],
                                                                     ["Conclusion","/flask-conclusion-practical/"],

                                                                     ],

                  

                  
                            }


    return TOPIC_DICT













if __name__ == "__main__":
    x = Content()

    print(x["Basics"])

    for each in x["Basics"]:
        print(each[1])
