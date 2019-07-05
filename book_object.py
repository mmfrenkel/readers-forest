from collections import namedtuple


class BookObject(namedtuple('Base', 'db_id isbn title author year')):
    pass

