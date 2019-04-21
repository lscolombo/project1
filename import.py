import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))

db = scoped_session(sessionmaker(bind=engine))

f = open("books.csv")
reader = csv.reader(f, delimiter=',')
#skip headers
next(reader)

#create tables:
#table user_account
db.execute(
    """CREATE TABLE user_accounts (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(20) NOT NULL)"""
)
db.commit()


#table book
db.execute(
    """CREATE TABLE books (
    book_isbn VARCHAR(13) PRIMARY KEY,
    title VARCHAR(50) NOT NULL,
    author VARCHAR(50) NOT NULL,
    year SMALLINT)"""
)
db.commit()


#table review
db.execute(
    """CREATE TABLE reviews (
    review_id SERIAL PRIMARY KEY,
    book_id VARCHAR(13) REFERENCES book (book_isbn) NOT NULL,
    user_id integer REFERENCES user_account (user_id) NOT NULL,
    review_text VARCHAR(300),
    review_rating SMALLINT NOT NULL)"""
)
db.commit()



#fill table books from .csv file
for isbn, title, author, year in reader:
    db.execute("INSERT INTO books (book_isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                {"isbn": isbn, "title": title, "author": author, "year": year})
    
    print(f"Added book {title} - ISBN: {isbn} - Author: {author} - Year: {year}")

    db.commit()