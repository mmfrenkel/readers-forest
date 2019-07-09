from flask import Flask, session, request, render_template, redirect, url_for, jsonify
from flask_session import Session
from book_database import BookDatabase
from goodreads import GoodreadsAPI

app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Create a Database
db = BookDatabase()
db.initiate_session()

# Goodreads API
goodreads_api = GoodreadsAPI()


@app.route("/")
def index():
    """ Default route; determines whether to send user to login or search based on if their session exists yet."""

    if session.get("first_name") is None:
        return redirect(url_for('login'))
    else:
        return redirect(url_for('search'))


@app.route("/login", methods=["GET"])
def login():
    """Default location to send new user to; sign in page"""

    return render_template("login.html", login_message="Please Sign In")


@app.route("/login", methods=["POST"])
def attempt_login():
    """User submitted a username and password from web page is checked against the user db and user
    is alerted if their credentials are not correct. """

    username = request.form.get("username")
    password = request.form.get("password")

    if db.correct_credentials(username, password):
        session["first_name"] = db.get_users_name_by_login(username, password)
        session["user_id"] = db.get_user_id_by_login(username, password)
        return redirect(url_for('search'))
    else:
        return render_template("login.html", login_message="Your username or password is incorrect. Try again.")


@app.route("/logout", methods=["GET"])
def logout():
    """ Logs user out of their session so they can log back in."""
    session.clear()
    return render_template("login.html", login_message="You've successfully logged out. Log back in?")


@app.route("/register", methods=["GET"])
def register():
    """Registration page for creating a new account."""
    return render_template("register.html", registration_message="Please submit your information below.")


@app.route("/register", methods=["POST"])
def attempt_registration():
    """Attempts to create a new user by taking fields submitted by user, checking if database already
    exists and, if not, creating the new user before asking them to sign in."""

    username = request.form.get("username")
    password = request.form.get("password")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")

    if first_name in ["", " "]:
        return render_template("register.html", registration_message="Please fill in a first name.")
    elif last_name in ["", " "]:
        return render_template("register.html", registration_message="Please fill in a last name.")
    elif username in ["", " "]:
        return render_template("register.html", registration_message="Please fill in a username.")
    elif password in ["", " "]:
        return render_template("register.html", registration_message="Please fill in a password.")
    elif db.username_exists(username):
        return render_template("register.html", registration_message="Sorry, this username already exists. Try again.")
    else:
        print("passed")
        db.add_new_user(first_name, last_name, username, password)
        return render_template("login.html", login_message="Successful Registration! Please Sign In")


@app.route("/search", methods=["GET"])
def search():
    """Default search page, accessible by user on login."""

    if session.get("first_name") is None:
        return redirect(url_for('login'))

    return render_template("search.html", user=session["first_name"], book_result=[], searched=False)


@app.route("/search", methods=["POST"])
def search_db():
    """Searches database for users request field, returning any match on isbn, author or title."""

    user_search = request.form.get("user_search")
    list_books = db.search_by_any(user_search)

    return render_template("search.html", user=session["first_name"], book_result=list_books, searched=True)


@app.route("/book-search/", methods=["POST"])
def find_book():
    isbn = request.form.get("book_isbn")
    return redirect(url_for('book', isbn=isbn))


@app.route("/book-review", methods=["POST"])
def review_book():

    isbn = request.form.get("book_isbn")
    rating = request.form.get("user_rating")
    review = request.form.get("user_review")

    book_db_id = db.get_book_db_id_by_isbn(isbn)
    db.add_user_review(user_db_id=session["user_id"], book_db_id=book_db_id, rating=rating, review=review)

    return redirect(url_for('book', isbn=isbn))


@app.route("/book/<string:isbn>", methods=["GET"])
def book(isbn):

    if session.get("first_name") is None:
        return redirect(url_for('login'))

    book_object = db.search_by_isbn(isbn)
    book_reviews = db.get_book_reviews(book_object.db_id)
    review_submitted = db.user_already_submitted_review(book_object.db_id, session['user_id'])

    average_goodreads_rating = goodreads_api.get_average_rating(isbn)
    number_goodreads_ratings = goodreads_api.get_number_ratings(isbn)

    return render_template(
        "book.html",
        user=session["first_name"],
        book=book_object,
        book_reviews=book_reviews,
        goodreads_rating=average_goodreads_rating,
        number_goodreads_reviews=number_goodreads_ratings,
        review_submitted=review_submitted
    )


@app.route("/api/<int:isbn>", methods=["GET"])
def book_by_isbn(isbn):
    """
    Available 'GET' endpoint for Reader's Forest API to return all information about a book.
    :param isbn: identifier for the book
    :return: json, representing book information
    """

    # Get book object, information
    found_book = db.search_by_isbn(str(isbn))

    # If book doesn't exist, then return 404 error
    if found_book is None:
        return jsonify({"Error": "ISBN number provided is unknown"}), 404

    # return book as formatted json
    return jsonify(
        {
            "title": found_book.title,
            "author": found_book.author,
            "year": found_book.year,
            "isbn": found_book.isbn,
            "review_count": found_book.review_count
        }
    )


@app.route("/api/<int:isbn>/author", methods=["GET"])
def author_by_isbn(isbn):
    """
    Available 'GET' endpoint for Reader's Forest API to get an author for a given book
    :param isbn: identifier for the book
    :return: json, representing book's author
    """

    # Get book object, information
    found_book = db.search_by_isbn(str(isbn))

    # If book doesn't exist, then return 404 error
    if found_book is None:
        return jsonify({"Error": "ISBN number provided is unknown"}), 404

    # return book as formatted json
    return jsonify(
        {
            "author": found_book.author
        }
    )


@app.route("/api/<int:isbn>/year", methods=["GET"])
def year_by_isbn(isbn):
    """
    Available 'GET' endpoint for Reader's Forest API to get the year published for a given book
    :param isbn: identifier for the book
    :return: json, representing book's year of publication
    """

    # Get book object, information
    found_book = db.search_by_isbn(str(isbn))

    # If book doesn't exist, then return 404 error
    if found_book is None:
        return jsonify({"Error": "ISBN number provided is unknown"}), 404

    # return book as formatted json
    return jsonify(
        {
            "year": found_book.year
        }
    )
