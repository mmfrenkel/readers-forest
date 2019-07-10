"""Creates the database tables, if not already existing"""

from book_database import BookDatabase

if __name__ == "__main__":
    db = BookDatabase()
    db.initialize()
