"""
Helpful classes defined to make facilitate information passage between the database and Jinja template variables.
"""
from collections import namedtuple


class BookObject(namedtuple('Base', 'db_id isbn title author year star_rating review_count')):
    pass


class ReviewObject(namedtuple('Base', 'db_id book_id username date_created rating review')):
    pass

