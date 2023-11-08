from flask import Flask, request, jsonify, render_template, redirect, url_for
import flask
from flask_cors import CORS
from urllib.parse import urlparse, urljoin
import os
from pathlib import Path
import flask_login
import secrets, string

data_folder = Path("backend/data/")

app = Flask(__name__)
CORS(app)
# This will enable CORS for all routes, which is a security issue. 
# Must be changed in production.

login_manager = flask_login.LoginManager()

login_manager.init_app(app)

login_manager.login_view = 'login'

app.secret_key = ''.join(secrets.choice(string.ascii_letters) for i in range(256))

not_protected = ["login", "logout"]

class_lookup = {}

for file in os.listdir(data_folder):
    if file.endswith(".csv") and "Major" in file:
        with open(str(data_folder.absolute()) + "/" + file, "r") as f:
            file_lines = [line.rstrip() for line in f.readlines()]
            class_lookup[file_lines[0]] = file[:-4]
print(class_lookup)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    # Ensure that the target URL is on the same domain as the host URL
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def redirect_back(default='home', **kwargs):
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return redirect(target)
    return redirect(url_for(default, **kwargs))

def validate_email(email):
    if email == None:
        return False
    email = email.lower()
    parts = email.split("@")
    if len(parts) != 2:
        return False
    if parts[1] != "my.erau.edu":
        return False
    for i in ["_", ".", "-", "@"]:
        if i in parts[0]:
            return False
    return True


def is_admin(email):  # temporary to redirect to admin page
    if "admin" in email:
        return True
    return False


def is_registrar(email):  # temporary to redirect to registrar page
    if "registrar" in email:
        return True
    return False


class User(flask_login.UserMixin):
    pass

@app.route('/')
@flask_login.login_required
def home():
    return render_template('index.html')

@app.route("/logout")
def logout():
    flask_login.logout_user()
    return "Logged out"


@app.route("/login", methods=["GET", "POST"])
def login():
    if flask.request.method == "GET":
        return render_template("login.html")

    email = flask.request.form["email"]
    if validate_email(email) and flask.request.form["password"] == "secret":
        user = User()
        user.id = email
        flask_login.login_user(user)
        # redirect_back func is broken, so here I will add full logic through if statements. I hate this.
        if is_admin(email):
            return redirect("/admin")
        if is_registrar(email):
            return redirect("/registrar")
        return redirect("/")
    return "Bad login"


@app.route("/admin")
@flask_login.login_required
def admin():
    return "Logged in as: " + flask_login.current_user.id


@login_manager.user_loader
def user_loader(email):
    if validate_email(email) == False:
        return

    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    email = request.form.get("email")
    if validate_email(email) == False:
        return

    user = User()
    user.id = email
    return user

# this is for debugging and needs to be removed for production
@app.route("/<degree>", methods=["GET"])
def get_degree_courses(degree):
    file_lines = get_required_courses(degree)

    if not file_lines:
        return jsonify(
            {
                "degree": None,
                "required_classes": None,
                "error": True,
                "error_message": "Degree not found.",
            }
        )

    degree_message = get_full_degree_name(degree)
    return jsonify(
        {
            "degree": degree_message,
            "required_classes": file_lines,
            "error": False,
            "error_message": None,
        }
    )


@app.route("/", methods=["POST"])
def post_degree_courses():
    data = request.json

    degree = data.get("degree")
    minors = data.get("minors")
    completed = data.get("completed")

    print(f"{degree = }")
    print(f"{minors = }")
    print(f"{completed = }")

    courses = get_required_courses(degree)

    for course in courses[:]:
        if course in completed:
            courses.remove(course)

    if not courses:
        return jsonify(
            {
                "degree": None,
                "required_classes": None,
                "error": True,
                "error_message": "Degree not found.",
            }
        )

    degree_message = get_full_degree_name(degree)
    return jsonify(
        {
            "degree": degree_message,
            "required_classes": courses,
            "error": False,
            "error_message": None,
        }
    )

@app.before_request
def before_request():
    if request.path.startswith('/static/') or request.endpoint == 'logout':
        return  # Allow access to static files and logout without being logged in
    if not flask_login.current_user.is_authenticated and request.endpoint != 'login':
        return redirect(url_for('login', next=request.url))

def get_required_courses(degree):
    try:
        with open(str(data_folder.absolute()) + "/" + degree + ".csv", "r") as f:
            file_lines = [line.rstrip() for line in f.readlines()]
            return file_lines[1:]
    except FileNotFoundError:
        return []

def get_full_degree_name(degree):
    try:
        with open(str(data_folder.absolute()) + "/" + degree + ".csv", "r") as f:
            file_lines = [line.rstrip() for line in f.readlines()]
            return file_lines[0]
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)