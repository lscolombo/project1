import os

from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
import json


app = Flask(__name__)

def page_not_found(e):
  return render_template('404.html'), 404

app.register_error_handler(404, page_not_found)

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

GOODREADS_KEY = "lQPRX6ne1CNGAV8raRov1w"

class Book:
    def __init__(self,isbn,title,year,author):
        self.isbn = isbn
        self.title = title
        self.year = year
        self.author = author




@app.route("/")
def index():
    return "Project 1: TODO"

@app.route("/logout", methods=["POST","GET"])
def logout():
    error = None
    session.clear()
    return render_template("login.html", error=error)

@app.route("/register", methods=["POST","GET"])
# def registration():
#     return render_template("registration.html")

#@app.route("/registrationcheck", methods=["POST","GET"])
def register():
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
                user = login_success(username,password)
                session["user_id"] = user['user_id']
                return redirect(url_for('search'))
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
    results = []
    if request.method == 'POST':
        keyword = request.form.get("keyword")
        results = book_search(keyword)
        if len(results) == 0:
            return render_template("404.html"),404
    return render_template('search.html',results=results)



def book_search(keyword):
    book_list = []
    #keyword = '%'+keyword+'%'
    results = db.execute("""SELECT * FROM book 
                            WHERE book_isbn like :keyword
                            OR UPPER(title) like :keyword
                            OR UPPER(author) like :keyword
                            ORDER BY title, author, book_isbn""", 
                            {"keyword":'%'+keyword.upper()+'%'})

    for result in results:
        isbn=result['book_isbn']
        title=result['title']
        year=result['year']
        author=result['author']
        new_book=Book(isbn,title,year,author)
        book_list.append(new_book)

    return(book_list)

@app.route("/details/<book_isbn>", methods=["GET"])
def details(book_isbn):
    error=None
    user_id = session["user_id"]
    dict_goodreads = get_goodreads_data(book_isbn)
    book = get_book_by_isbn(book_isbn)
    reviews = get_reviews(book_isbn)
    allow_review = single_book_review_success(user_id,book_isbn)
    flash(error)
    return render_template('book.html',error=error,book=book, avg_rating=dict_goodreads["avg_rating"],ratings_count=dict_goodreads["ratings_count"], reviews=reviews, allow_review=allow_review)

@app.route("/details/<book_isbn>", methods=["GET","POST"])
def reviews(book_isbn):
    error=None
    dict_goodreads = get_goodreads_data(book_isbn)
    user_id = session["user_id"]
    review = request.form.get("review")
    rating = request.form['rating']
    book = get_book_by_isbn(book_isbn)
    error = add_review(book_isbn,user_id,review,rating)
    reviews = get_reviews(book_isbn)
    allow_review = single_book_review_success(user_id,book_isbn)
    flash(error)
    return render_template('book.html',error=error,book=book, avg_rating=dict_goodreads["avg_rating"],ratings_count=dict_goodreads["ratings_count"], reviews=reviews, allow_review=allow_review)

@app.route("/api/<book_isbn>", methods=["GET"])
def api(book_isbn):
    json = get_book_api_data(book_isbn)
    return(json)


def get_book_cover(book_isbn):
    res = ("http://covers.openlibrary.org/b/isbn/{book_isbn}-M.jpg",book_isbn)
    return(res)

def get_goodreads_data(book_isbn):
    try:
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": GOODREADS_KEY, "isbns": book_isbn})
        response = res.json()
        avg_rating = response['books'][0]['average_rating']
        ratings_count = response['books'][0]['work_ratings_count']
    except:
        avg_rating='Not available'
        ratings_count = 'Not available'
    dict_goodreads_data = {"avg_rating": avg_rating,
                        "ratings_count": ratings_count}
    return(dict_goodreads_data)

def get_book_by_isbn(book_isbn):
    consult = db.execute("SELECT * FROM book WHERE book_isbn = :book_isbn",
                        {"book_isbn":book_isbn}).fetchone()
    isbn=consult['book_isbn']
    title=consult['title']
    year=consult['year']
    author=consult['author']
    book=Book(isbn,title,year,author)
    return(book)

def add_review(book_isbn,user_id,review,rating):
    error = None
    if single_book_review_success(user_id,book_isbn):
        db.execute("""INSERT INTO review (book_id,user_id,review_text,review_rating) 
                    VALUES (:book_id, :user_id, :review_text, :review_rating)""",
                    {"book_id": book_isbn, "user_id": user_id, "review_text": review, "review_rating": rating})
        db.commit()
    else:
        error='The user has already written a review for the selected book'
    return(error)

def single_book_review_success(user_id,book_isbn):
    result = db.execute("""SELECT review_text, review_rating FROM review
                        WHERE book_id = :book_id AND user_id=:user_id""",
                        {"user_id":user_id,"book_id":book_isbn}).fetchone()
    if result is None:
        return(True)
    else:
        return(False)

def get_reviews(book_isbn):
    results = db.execute("""SELECT u.username, r.review_text, r.review_rating
                        FROM review r 
                        INNER JOIN user_account u on u.user_id = r.user_id
                        WHERE r.book_id = :book_isbn""",
                        {"book_isbn":book_isbn}).fetchall()
    return(results)

def get_book_api_data(book_isbn):
    result = jsonify(dict(db.execute("""SELECT b.title, b.author, b.year, 
                        b.book_isbn, count(r.review_id), avg(r.review_rating)
                        FROM book b
                        INNER JOIN review r on r.book_id = b.book_isbn
                        WHERE b.book_isbn = :book_isbn
                        GROUP BY b.title, b.author, b.year, 
                        b.book_isbn""", 
                        {"book_isbn":book_isbn}).fetchone()))
    return(result)