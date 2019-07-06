import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from objects import BookObject


class DatabaseWorker:

    def __init__(self):
        self.session = None
        self.engine = None

    def initialize_database(self):
        """Main method to set up new database tables from scratch and inserts book information from file."""

        try:
            self.initiate_session()
            self.create_all_tables()
            self.insert_books_from_file()
            self.close_session()
        except Exception as e:
            print(f"Failed to properly initialized database due to {e}")

    def initiate_session(self):
        """Creates the SQLAlchemy Session"""

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
        """Creates all database tables at once."""

        self.create_user_table()
        self.create_books_table()
        self.create_reviews_table()
        self.create_user_saved_books()

    def insert_books_from_file(self, book_file="books.csv"):
        """
        Imports a csv file containing book data (comma-delimited) and inserts each line into the
        books database. Assumes that a file called "books.csv" exists in the same directory level,
        but another path can be passed.
        """

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
        """Creates 'users' table from scratch, if doesn't exist yet."""

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
        """Creates 'books' table from scratch, if doesn't exist yet."""

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
        """Creates 'book_reviews' table from scratch, if doesn't exist yet."""

        if self.engine.dialect.has_table(self.engine, 'book_reviews'):
            print("Note 'book_reviews' table already exists")
            return

        print("Creating 'book_reviews' Table")
        self.session.execute(
            """CREATE TABLE book_reviews ( 
                id SERIAL PRIMARY KEY,
                book_id INT REFERENCES books,
                user_id INT REFERENCES users,
                date_created DATE,
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
        """
        Returns true if the username, password combination provided is in the db for
        1 and only 1 distinct entry.
        :param username
        :param password
        :return: boolean for 'was successful login'
        """

        if self.session.execute("SELECT username FROM users WHERE username = :username AND password = :password",
                      {"username": username, "password": password}).rowcount == 1:
            return True
        return False

    def get_users_name_by_login(self, username, password):
        """Obtains the user's name as a string based on their login credentials"""

        return self.session.execute("SELECT first_name FROM users WHERE username = :username AND password = :password",
                                    {"username": username, "password": password}).fetchone()['first_name']

    def get_user_id_by_login(self, username, password):
        """Obtains the user's name as a string based on their login credentials"""

        return self.session.execute("SELECT id FROM users WHERE username = :username AND password = :password",
                                    {"username": username, "password": password}).fetchone()['id']

    def get_username_by_id(self, user_db_id):
        """Obtains the user's name as a string based on their database id."""

        return self.session.execute("SELECT id FROM users WHERE id = :db_id", {"db_id": user_db_id}).fetchone()['username']

    def add_new_user_to_db(self, first_name, last_name, username, password):
        """
        Adds a new Reader's Forest user to the database (user table)
        :param first_name: first name of new user
        :param last_name: last name of new user
        :param username: submitted username
        :param password: submitted password
        :return: None
        """

        try:
            self.session.execute(
                "INSERT INTO users (first_name, last_name, username, password) "
                "VALUES (:first_name, :last_name, :username, :password)",
                {"first_name": first_name, "last_name": last_name, "username": username, "password": password, }
            )
            self.session.commit()
        except Exception as e:
            print(f"Could not add new user to the database due to: {e}")

    def search_book_database_by_any(self, item):
        """
        Searches the book database to locate any 'matching' items based on LIKE queries for title, isbn and author
        and returns a list of book objects. Note that date is unsupported
        :param item: any item submitted by user
        :return: list of book tuple Objects that match the search item
        """

        query_item = '%' + str(item) + '%'
        query = "SELECT * FROM books WHERE ((isbn LIKE :isbn) OR (title LIKE :title) OR (author LIKE :author));"
        book_tuples = self.session.execute(query, {"isbn": query_item, "title": query_item, "author": query_item}).fetchall()

        list_books = list()
        for book in book_tuples:
            book_object = BookObject(
                db_id=book[0],
                isbn=book[1],
                title=book[2],
                author=book[3],
                year=book[4],
                star_rating=3
            )
            list_books.append(book_object)

        return list_books

    def search_book_database_by_isbn(self, isbn):
        """
        Searches the book database to locate books based on their isbn identification number.
        Note that this assumes that every isbn number is distinct
        :param isbn: any item submitted by user
        :return: list of book tuple Objects that match the search item
        """

        query = "SELECT * FROM books WHERE isbn = :isbn;"
        book_tuples = self.session.execute(query, {"isbn": isbn}).fetchall()

        if not book_tuples:
            return None

        # assume one result (1 element in list of tuples)
        book_tuple = book_tuples[0]
        book = BookObject(
            db_id=book_tuple[0],
            isbn=book_tuple[1],
            title=book_tuple[2],
            author=book_tuple[3],
            year=book_tuple[4],
            star_rating=3
        )
        return book

    def get_book_reviews(self, book_db_id):
        """
        Retrieves all book reviews based on the books database id.
        :param db_book_id:  unique identifier (id) for the book in the database (id from 'books' table)
        :return: list of Review objects
        """

        query = "SELECT * FROM book_reviews WHERE book_id = :book_id;"
        review_tuples = self.session.execute(query, {"book_id": book_db_id}).fetchall()

        if not review_tuples:
            return None

        list_reviews = list()
        for review in review_tuples:
            review_object = BookObject(
                db_id=review[0],
                book_id=review[1],
                username=self.get_username_by_id(review[2]),
                date_created=review[3],
                rating=review[4],
                review=review[5]
            )
            list_reviews.append(review_object)

        return list_reviews

    def user_already_submitted_review(self, book_db_id, user_db_id):
        """
        Returns True if a user has already submitted an id for a book.
        :param book_db_id
        :param user_db_id
        :return: boolean representing if review has already been submitted
        """
        query = "SELECT * FROM book_reviews WHERE book_id = :book_id AND user_id = :user_id;"
        if self.session.execute(query, {"book_id": book_db_id, "user_id":user_db_id}).fetchall():
            return True
        else:
            return False

    def close_session(self):
        self.session.close()

