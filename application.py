import os

from flask import Flask, session, render_template, request, redirect, url_for, flash
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
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        password_confirmation = request.form.get("password_confirmation")
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif password != password_confirmation:
            error = 'Passwords did not match.'
        else:
            if user_exists(username):
                error = 'Username is already registered.'
            else:
                #insert new user into database
                insert_user(username,password)
                return redirect(url_for('login'))
        flash(error)
    return render_template("registration.html")


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
    error = None
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        error = None
        user = login_success(username,password)
        if user is not None:
            #correct login
            session.clear()
            session["user_id"] = user['user_id']
            return redirect(url_for('search'))
        else:
            #incorrect login
            error = 'There has been a problem with your credentials. Please, try again.'

        flash(error)

    return render_template("login.html", error=error)


def login_success(username,password):
    user = db.execute("""SELECT * FROM user_account 
                WHERE username = :username AND password = :password""",
                {"username": username, "password":password}).fetchone()
    return(user)

@app.route("/search", methods=["POST","GET"])
def search():
    if request.method == 'POST':
        keyword = request.form.get("keyword")
        results = book_search(keyword)
        return render_template('search.html',results=results)
        if results.rowcount == 0:
            results = ['No results found.']
    return render_template('search.html')

def book_search(keyword):
    #keyword = '%'+keyword+'%'
    results = db.execute("""SELECT * FROM book 
                            WHERE book_isbn like :keyword
                            OR UPPER(title) like :keyword
                            OR UPPER(author) like :keyword
                            ORDER BY title, author, book_isbn""", 
                            {"keyword":'%'+keyword.upper()+'%'})
    return(results)

@app.route("/details/<string:book_isbn>", methods=["GET"])
def details(book_isbn):
    return str(book_isbn)