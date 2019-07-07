from flask import Flask, session, request, render_template, redirect, url_for
from flask_session import Session
from database_worker import DatabaseWorker

app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Create a DatabaseWorker
db = DatabaseWorker()
db.initiate_session()


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

    if db.login_successful(username, password):
        session["first_name"] = db.get_users_name_by_login(username, password)
        session["user_id"] = db.get_user_id_by_login(username, password)
        return redirect(url_for('search'))
    else:
        return render_template("login.html", login_message="Your username or password is incorrect. Try again.")


@app.route("/logout", methods=["Get"])
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

    if db.username_exists(username):
        return render_template("register.html", registration_message="Sorry, this username already exists. Try again.")
    else:
        db.add_new_user_to_db(first_name, last_name, username, password)
        return render_template("login.html", login_message="Successful Registration! Please Sign In")


@app.route("/search", methods=["GET"])
def search():
    """Default search page, accessible by user on login."""

    if session.get("first_name") is None:
        return redirect(url_for('login'))

    return render_template("search.html", user=session["first_name"], book_result=[])


@app.route("/search", methods=["POST"])
def search_db():
    """Searches database for users request field, returning any match on isbn, author or title."""

    user_search = request.form.get("user_search")
    list_books = db.search_book_database_by_any(user_search)

    return render_template("search.html", user=session["first_name"], book_result=list_books)


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
    db.add_user_review_to_db(user_db_id=session["user_id"], book_db_id=book_db_id, rating=rating, review=review)

    return redirect(url_for('book', isbn=isbn))


@app.route("/book/<string:isbn>", methods=["GET"])
def book(isbn):

    if session.get("first_name") is None:
        return redirect(url_for('login'))

    book_object = db.search_book_database_by_isbn(isbn)
    book_reviews = db.get_book_reviews(book_object.db_id)
    review_submitted = db.user_already_submitted_review(book_object.db_id, session['user_id'])

    return render_template("book.html", user=session["first_name"], book=book_object, book_reviews=book_reviews,
                           review_submitted=review_submitted)

