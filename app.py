from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

#We use helpers similar to Finance where an apology is given through errors
from helpers import apology, login_required


#Configure Applicaton
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods = ["GET", "POST"])
def register():
    """Register user"""
    # Go through the two methods of get or post
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Special touch of making accounts safer when registering by requiring an uppercase lower case and at least a length of 8
        if not (any(case.isupper() for case in password) and any(case.islower() for case in password) and len(password) > 7):
            return apology("For security, please make sure your password contains at least 1 lowercase, 1 uppercase, and is at least 8 characters long.")
        # Our several conditions if the user inputs are invalid
        if password != confirmation:
            return apology("The passwords do not match")
        if not username:
            return apology("Please enter a username")
        if not password:
            return apology("Please enter a password")
        if not confirmation:
            return apology("Please confirm your password")

        # Hash the user's password
        hash = generate_password_hash(password)

        # Upadting our new user into the database
        try:
            new_user = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
        except:
            return apology("The username already exists")

        session["user_id"] = new_user

    return redirect("/")

@app.route("/general")
@login_required
def general():
    #load movie database that we created to hold all the facts about the marvel movies
    movies_db = db.execute("SELECT * FROM movies")
    return render_template("general.html", movies = movies_db)

@app.route("/ratings", methods = ["GET", "POST"])
@login_required
def ratings():

        #These variables are all necessary to update our scores database
        user_id = session["user_id"]
        user_score = request.form.get("user_score")
        name = request.form.get("movie_title")
        comment = request.form.get("comment")

        #With each new row, update the user score name comment
        db.execute("INSERT INTO scores (user_id, user_score, name, comment) VALUES (?, ?, ?, ?)", user_id, user_score, name, comment)
        #We are going to use next to update whoever submitted a score and match their username
        next = db.execute("UPDATE scores SET username = users.username FROM users WHERE scores.user_id = users.id")
        db.execute("INSERT INTO scores (username) VALUES (?)", next)
        #I had a problem where the ratings page loaded many times before the submit button was hit, but the methods were difficult to solve this problem, so we can just remove all the null columns
        db.execute("DELETE FROM scores WHERE (comment) IS NULL")

        return render_template("ratings.html")

@app.route("/discussion")
@login_required
def discussion():
    #We need the scores to get info from ratings
    scores_db = db.execute("SELECT * FROM scores ORDER BY id DESC")
    return render_template("discussion.html", scores = scores_db)


@app.route("/")
@login_required
def index():
    return render_template("layout.html")


