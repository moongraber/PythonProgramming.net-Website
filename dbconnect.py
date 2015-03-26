import MySQLdb


def connection():
    conn = MySQLdb.connect(host="localhost", # your host, usually localhost
                     user="", # your username
                      passwd="", # your password
                      db="") # name of the data base
    c = conn.cursor()

    return c, conn
