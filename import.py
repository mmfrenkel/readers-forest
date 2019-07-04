import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


class BookDatabaseInserter:

    def __init__(self):
        self.session = None
        self.engine = None

    def run(self):
        self.initiate_session()
        self.create_all_tables()
        self.insert_books_from_file()
        self.close_session()

    def initiate_session(self):
        print("Initiating SQLAlchemy Session")

        try:
            self.engine = create_engine(os.getenv("DATABASE_URL"))
            self.session = scoped_session(sessionmaker(bind=self.engine))
        except TypeError as te:
            print(f"Failed to create session, please make sure DATABASE_URL env variable is set. See more: {te}")

    def create_all_tables(self):
        """Creates all database tables at once"""

        if not self.session:
            self.initiate_session()

        self.create_user_table()
        self.create_books_table()
        self.create_reviews_table()
        self.create_user_saved_books()

    def insert_books_from_file(self, book_file="books.csv"):
        """Imports a csv file containing book data (comma-delimited) and inserts each line into the
        books database."""

        if not self.session:
            self.initiate_session()

        print("Inserting books into 'books' table from .csv file")
        try:
            f = open(book_file)
            reader = csv.reader(f)
            next(reader)            # skip header
        except FileNotFoundError:
            print("Please make sure that the books.csv file is in the correct spot in your repository.")

        for isbn, title, author, year in reader:
            insert_statement = "INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)"
            self.session.execute(insert_statement, {"isbn": isbn, "title": title, "author": author, "year": year})

        try:
            self.session.commit()
        except Exception as e:
            print(f"Failed to commit changes to the database due to {e}")

    def create_user_table(self):

        if self.engine.dialect.has_table(self.engine, 'users'):
            print("Note 'users' table already exists")
            return

        print("Creating 'users' Table")
        self.session.execute(
            """CREATE TABLE users ( 
                id SERIAL PRIMARY KEY,
                username VARCHAR NOT NULL,
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

    def close_session(self):
        self.session.close()


if __name__ == "__main__":
    db_runner = BookDatabaseInserter()
    db_runner.run()

