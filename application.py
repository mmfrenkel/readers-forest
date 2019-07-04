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
        return render_template("login.html")
    else:
        return render_template("search.html")


@app.route("/register", methods=["POST", "GET"])
def register():
    return render_template("register.html")


@app.route("/search")
def search():
    return render_template("search.html", user=session["first_name"])


@app.route("/books/<isbn>")
def book(isbn):
    return render_template("book.html", books=books)


def check_username_password_exist():
