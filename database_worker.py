import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


class DatabaseWorker:

    def __init__(self):
        self.session = None
        self.engine = None

    def initialize_database(self):
        try:
            self.initiate_session()
            self.create_all_tables()
            self.insert_books_from_file()
            self.close_session()
        except Exception as e:
            print(f"Failed to properly initialized database due to {e}")

    def initiate_session(self):
        print("Initiating SQLAlchemy Session")

        # Check for environment variable
        if not os.getenv("DATABASE_URL"):
            raise RuntimeError("DATABASE_URL is not set")

        try:
            self.engine = create_engine(os.getenv("DATABASE_URL"))
            self.session = scoped_session(sessionmaker(bind=self.engine))
        except Exception as te:
            print(f"Failed to create session, See more: {te}")

    def create_all_tables(self):
        """Creates all database tables at once"""

        self.create_user_table()
        self.create_books_table()
        self.create_reviews_table()
        self.create_user_saved_books()

    def insert_books_from_file(self, book_file="books.csv"):
        """Imports a csv file containing book data (comma-delimited) and inserts each line into the
        books database."""

        print("Inserting books into 'books' table from .csv file")
        try:
            f = open(book_file)
            reader = csv.reader(f)
            next(reader)   # skip header
        except FileNotFoundError:
            print("Please make sure that the books.csv file is in the correct spot in your repository.")

        for isbn, title, author, year in reader:
            insert_statement = "INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)"
            self.session.execute(insert_statement, {"isbn": isbn, "title": title, "author": author, "year": year})

        self.session.commit()

    def create_user_table(self):

        if self.engine.dialect.has_table(self.engine, 'users'):
            print("Note 'users' table already exists")
            return

        print("Creating 'users' Table")
        self.session.execute(
            """CREATE TABLE users ( 
                id SERIAL PRIMARY KEY,
                first_name VARCHAR NOT NULL,
                last_name VARCHAR NOT NULL,
                username VARCHAR UNIQUE NOT NULL,
                password VARCHAR NOT NULL
            );"""
        )
        self.session.commit()

    def create_books_table(self):

        if self.engine.dialect.has_table(self.engine, 'books'):
            print("Note 'books' table already exists")
            return

        print("Creating 'books' Table")
        self.session.execute(
            """CREATE TABLE books ( 
                id SERIAL PRIMARY KEY,
                isbn VARCHAR UNIQUE,
                title VARCHAR NOT NULL,
                author VARCHAR NOT NULL,
                year INT NOT NULL
            );"""
        )
        self.session.commit()

    def create_reviews_table(self):

        if self.engine.dialect.has_table(self.engine, 'book_reviews'):
            print("Note 'book_reviews' table already exists")
            return

        print("Creating 'book_reviews' Table")
        self.session.execute(
            """CREATE TABLE book_reviews ( 
                id SERIAL PRIMARY KEY,
                user_id INT REFERENCES users,
                rating FLOAT,
                review VARCHAR
            );"""
        )

        self.session.commit()

    def create_user_saved_books(self):

        if self.engine.dialect.has_table(self.engine, 'saved_books'):
            print("Note 'saved_books' table already exists")
            return

        print("Creating 'saved_books' Table")
        self.session.execute(
                """CREATE TABLE saved_books ( 
                    user_id INT REFERENCES users,
                    book_id INT REFERENCES books
            );"""
        )
        self.session.commit()

    def username_exists(self, username):
        """Returns true if provided username exists in the users database"""

        if self.session.execute("SELECT username FROM users WHERE username = :username",
                                {"username": username}).rowcount == 0:
            return False
        return True

    def login_successful(self, username, password):
        """Returns true if the username, password combination provided is in the db for
        1 and only 1 distinct entry"""

        if self.session.execute("SELECT username FROM users WHERE username = :username AND password = :password",
                      {"username": username, "password": password}).rowcount == 1:
            return True
        return False

    def get_users_first_name(self, username, password):
        """Obtains the user's name as a string """

        return self.session.execute("SELECT first_name FROM users WHERE username = :username AND password = :password",
                                    {"username": username, "password": password}).fetchone()['first_name']

    def add_new_user_to_db(self, first_name, last_name, username, password):

        try:
            self.session.execute(
                "INSERT INTO users (first_name, last_name, username, password) "
                "VALUES (:first_name, :last_name, :username, :password)",
                {"first_name": first_name, "last_name": last_name, "username": username, "password": password, }
            )
            self.session.commit()
        except Exception as e:
            print(f"Could not add new user to the database due to: {e}")

    def close_session(self):
        self.session.close()

