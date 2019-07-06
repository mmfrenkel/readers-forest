from collections import namedtuple


class BookObject(namedtuple('Base', 'db_id isbn title author year star_rating')):
    pass


class ReviewObject(namedtuple('Base', 'db_id book_id username date_created rating review')):
    pass

