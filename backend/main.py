from flask import Flask, request, jsonify, render_template, redirect, url_for, Response, abort, send_file
import flask
from flask_cors import CORS
from urllib.parse import urlparse, urljoin
import os, io
from pathlib import Path
import flask_login
import secrets, string
import math
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

data_folder = Path("backend/data/")

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
# This will enable CORS for all routes, which is a security issue.
# Must be changed in production.

login_manager = flask_login.LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

app.secret_key = "".join(secrets.choice(string.ascii_letters) for i in range(256))

not_protected = ["login", "logout"]

class_lookup = {}


# there's no way to properly get a student ID, so we're going to cheat a little for demonstration purposes
def get_student_id(input_string):
    if "advisor" in input_string or "registrar" in input_string:
        return "N/A"
    # Convert each character to its ASCII value and sum them up
    sum_ascii = sum(ord(char) for char in input_string)

    # Map the sum to the range 260000 to 270000
    encoded_value = 260000 + (sum_ascii % 10000)

    return encoded_value


for file in os.listdir(data_folder):
    if file.endswith(".csv"):
        with open(str(data_folder.absolute()) + "/" + file, "r") as f:
            file_lines = [line.rstrip() for line in f.readlines()]
            class_lookup[file_lines[0]] = file[:-4]
print(class_lookup)
reverse_class_lookup = {v: k for k, v in class_lookup.items()}
print(reverse_class_lookup)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    # Ensure that the target URL is on the same domain as the host URL
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def redirect_back(default="home", **kwargs):
    for target in request.args.get("next"), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return redirect(target)
    return redirect(url_for(default, **kwargs))


def draw_centered_string(c, text, y, font_name="Helvetica", font_size=12):
    """
    Draw a string centered on the page in a ReportLab canvas.

    :param c: The canvas to draw on.
    :param text: The text string to center.
    :param y: The y-coordinate on the canvas.
    :param font_name: The font name to use.
    :param font_size: The font size to use.
    """
    # Set the font for the canvas
    c.setFont(font_name, font_size)

    # Measure text width
    text_width = pdfmetrics.stringWidth(text, font_name, font_size)

    # Get the page width from the canvas
    page_width = c._pagesize[0]

    # Calculate the x coordinate
    x = (page_width - text_width) / 2

    # Draw the string on the canvas
    c.drawString(x, y, text)


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


class User(flask_login.UserMixin):
    def is_advisor(self):
        if "advisor" in self.id:
            return True
        return False

    def is_registrar(self):
        if "registrar" in self.id:
            return True
        return False


@app.route("/")
@flask_login.login_required
def home():
    return render_template("index.html")


@app.route("/logout")
def logout():
    flask_login.logout_user()
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if flask.request.method == "GET":
        return render_template("login.html")

    email = flask.request.form["email"]
    if validate_email(email) and flask.request.form["password"] == "a":
        user = User()
        user.id = email
        flask_login.login_user(user)
        # redirect_back func is broken, so here I will add full logic through if statements. I hate this.
        if user.is_advisor():
            return redirect("/")
        if user.is_registrar():
            return redirect("/data")
        return redirect("/")
    return redirect("/login")


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


@app.route("/", methods=["POST"])
def post_degree_courses():
    data = request.json

    degree = data.get("degree")
    minors = data.get("minors")
    completed = data.get("completed")
    
    degree = class_lookup[degree + " (Major)"]

    courses = get_required_courses(degree)
    
    if minors != "":
        for minor in minors.split(","):
            while minor[0] == " ":
                minor = minor[1:]
            courses += get_required_courses(class_lookup[minor + " (Minor)"])   

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
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    print(width, height)
    c.setFont("Helvetica", 12)

    # Header
    c.setFontSize(16)
    draw_centered_string(
        c, "EMBRY-RIDDLE AERONAUTICAL UNIVERSITY", height - 50, font_size=16
    )
    draw_centered_string(c, degree_message, height - 70, font_size=16)

    # Student Information
    c.setFontSize(10)
    c.drawString(50, height - 100, f"Student email: {flask_login.current_user.id}")
    c.drawString(
        50, height - 112, f"Student ID: {get_student_id(flask_login.current_user.id)}"
    )  # ohohoho im so sneaky
    c.drawPath

    # Table for Course Information
    data = [
        ["COURSE NUMBER/TITLE", "Pre-Requisites", "Credit", "Required", "Comments"]
    ]
    needed_total = 0
    completed_total = 0
    for course in courses:
        satisfied = False
        prereq_satisfied = True
        if course in completed:
            satisfied = True
        for prereq in course.split(",")[1:]:
            if prereq not in completed:
                prereq_satisfied = False
        if len(course.split(",")) > 2:
            prereq_string = (
                course.split(",")[2].replace(" ", " and ").replace("|", " or ")
            )
        else:
            prereq_string = "None"
        if satisfied == True:
            credits = course.split(",")[0]
            completed_total += int(credits)
            needed = "0"
        else:
            credits = "0"
            needed = course.split(",")[0]
            needed_total += int(needed) 
        satisfied_string = "Unsatisfied" if not satisfied else "Satisfied"
        if not prereq_satisfied:
            satisfied_string += " - " + "Prereqs not satisfied"
        else:
            satisfied_string += " - " + "Prereqs satisfied"
        data.append(
            [course.split(",")[1], prereq_string, credits, needed, satisfied_string]
        )  # it works, not changing, don't touch it
    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    table.wrapOn(c, width, height)
    table.drawOn(c, 50, height - 117 - table._height)
    
    table2 = Table([["Total Credits", "Credits Needed", "Credits Satisfied", "Estimated Semesters until Graduation"], [completed_total + needed_total, needed_total, completed_total, math.ceil(needed_total / 15)]])
    table2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    w, h = table.wrap(0, 0)
    table2.wrapOn(c, width, height)
    table2.drawOn(c, 50, height - 117 - table._height - table2._height)

    # Footer
    c.setFontSize(8)
    c.drawString(width - 50, 30, "Page | 1")
    c.drawString(10, 30, "This is not an official transcript or report.")
    c.drawString(10, 22, "This PDF was generated by a student project,") 
    c.drawString(10, 14, "and should not be used as an indication of your academic standing.")

    # Save the PDF
    c.save()
    buffer.seek(0)

    # Create a response object and send the PDF as a file attachment
    return Response(
        buffer,
        headers={
            "Content-Disposition": "attachment; filename=report.pdf",
            "Content-Type": "application/pdf",
        },
    )


@app.before_request
def before_request():
    if request.path.startswith("/static/") or request.endpoint == "logout":
        return  # Allow access to static files and logout without being logged in
    if not flask_login.current_user.is_authenticated and request.endpoint != "login":
        return redirect(url_for("login", next=request.url))


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
    
@app.route('/data', defaults={'req_path': ''})
@app.route('/<path:req_path>')
def dir_listing(req_path):
    BASE_DIR = 'backend/data/'

    # Joining the base and the requested path
    abs_path = os.path.join(BASE_DIR, req_path)
    print(abs_path)
    if "data/data" in abs_path:
        abs_path = abs_path.replace("data/data", "data/") # what the fuck?
        print(abs_path)
    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        print("404")
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        print("file")
        abs_path = abs_path.replace("backend/", "")
        print(abs_path)
        return send_file(abs_path)
    

    # Show directory contents
    files = os.listdir(abs_path)
    print("dir")
    return render_template('files.html', files=files)


if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)
