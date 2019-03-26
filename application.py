import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return "Project 1: TODO"

@app.route("/register", methods=["POST","GET"])
# def registration():
#     return render_template("registration.html")

#@app.route("/registrationcheck", methods=["POST","GET"])
def registrationcheck():
    username = request.form.get("username")
    password = request.form.get("password")
    password_confirmation = request.form.get("password_confirmation")
    error = ''

    if not username:
        error = 'Username is required.'
        return render_template("registration.html", error=error)
    elif not password:
        error = 'Password is required.'
        return render_template("registration.html", error=error)
    elif password != password_confirmation:
        error = 'Passwords did not match.'
        return render_template("registration.html", error = error)
    else:
        if user_exists(username):
            error = 'Username is already registered.'
            return render_template("registration.html", error=error)            
        else:
            #insert new user into database
            insert_user(username,password)
            return render_template("search.html", username=username, password=password)

#    return render_template("registration.html", error=error)            

def user_exists(username):
    exists = db.execute("""SELECT user_id FROM user_account
                        WHERE username = :username""",
                        {"username": username}).fetchone()
    if exists is not None:
        #user already exists
        return True
    else:
        #user does not exist
        return False

def insert_user(username,password):
    db.execute("""INSERT INTO user_account (username,password) 
                VALUES (:username, :password)""",
                {"username": username, "password": password})
    db.commit()

@app.route("/login", methods=["POST","GET"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    success = login_success(username,password)
    if success:
        #user exists
        return render_template("search.html")
    elif success == 1:
        #user does not exist in the database
        return render_template("loginerror.html")


def login_success(username,password):
    success = db.execute("""SELECT user_id FROM user_account 
                WHERE username = :username AND password = :password""",
                {"username": username, "password":password}).fetchone()
    return(success)

""" @app.route("/search", methods=["POST", "GET"])
def search():
    book_search = request.form.get("book_search")

def search_db(book_search)
    #db.execute..
 """