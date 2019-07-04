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
def login():
    if session.get("first_name") is None:
        return render_template("login.html", login_message="Please Sign In")
    else:
        return render_template("search.html", first_name=session["first_name"])


@app.route("/login", methods=["POST", "GET"])
def attempt_login():

    if request.method == "GET":
        return redirect(url_for('login'))

    # get information from form
    username = request.form.get("username")
    password = request.form.get("password")

    if db.login_successful(username, password):
        session["first_name"] = db.get_users_first_name(username, password)
        return redirect(url_for('search'))
    else:
        return render_template("login.html", login_message="Your username or password is incorrect. Try again.")


@app.route("/logout", methods=["Get"])
def logout():
    session.clear()
    return render_template("login.html", login_message="You've successfully logged out.")


@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html", registration_message="Please submit your information below.")


@app.route("/register", methods=["POST"])
def attempt_registration():

    username = request.form.get("username")
    password = request.form.get("password")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")

    if db.username_exists(username):
        return render_template("register.html", registration_message="Sorry, this username already exists. Try again.")
    else:
        db.add_new_user_to_db(first_name, last_name, username, password)
        return render_template("login.html", login_message="Successful Registration! Please Sign In")


@app.route("/search")
def search():
    return render_template("search.html", user=session["first_name"])


@app.route("/books/<isbn>")
def book(isbn):
    return render_template("book.html")




