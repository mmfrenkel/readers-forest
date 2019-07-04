import os
from flask import Flask, session, request, render_template
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def login():
    if session.get("first_name") is None:
        return render_template("login.html", login_message="Please Sign In")
    else:
        return render_template("search.html", first_name=session["first_name"])


@app.route("/login-attempt", methods=["POST", "GET"])
def attempt_login():

    if request.method == "GET":
        return render_template("login.html", login_message="Please Sign In")

    # get information from form
    username = request.form.get("username")
    password = request.form.get("password")

    if login_successful(username, password):
        session["first_name"] = get_users_first_name(username, password)
        return render_template("search.html", first_name=session["first_name"])
    else:
        return render_template("login.html", login_message="Your username or password is incorrect. Try again.")


@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html", registration_message="Please submit your information below.")


@app.route("/registration-attempt", methods=["POST", "GET"])
def attempt_registration():

    if request.method == "GET":
        return render_template("register.html", registration_message="Please submit your information below.")

    username = request.form.get("username")
    password = request.form.get("password")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")

    if username_exists(username):
        return render_template("register.html", registration_message="This username already exists. Try again.")
    else:
        add_new_user_to_db(username, password, first_name, last_name)
        return render_template("login.html", login_message="Please Sign In")


@app.route("/search")
def search():
    return render_template("search.html", user=session["first_name"])


@app.route("/books/<isbn>")
def book(isbn):
    return render_template("book.html")


def username_exists(username):
    """Returns true if provided username exists in the users database"""

    if db.execute("SELECT username FROM users WHERE username = :username", {"username": username}).rowcount == 0:
        return False
    return True


def login_successful(username, password):
    """Returns true if the username, password combination provided is in the db for
    1 and only 1 distinct entry"""

    if db.execute("SELECT username FROM users WHERE username = :username AND password = :password",
                  {"username": username, "password": password}).rowcount == 1:
        return True
    return False


def get_users_first_name(username, password):
    """Obtains the user's name as a string """

    return db.execute("SELECT first_name FROM users WHERE username = :username AND password = :password",
                      {"username": username, "password": password}).fetchone()['first_name']


def add_new_user_to_db(first_name, last_name, username, password):

    try:
        db.execute(
            "INSERT INTO users (first_name, last_name, username, password) "
            "VALUES (:first_name, :last_name, :username, :password)",
            {"first_name": first_name, "last_name": last_name, "username": username, "password": password, }
        )
        db.commit()
    except Exception as e:
        print(f"Could not add new user to the database due to: {e}")


