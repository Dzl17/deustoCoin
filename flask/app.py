from flask import Flask, url_for, render_template, request, redirect
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
import json
import os
import sqlite3
from db import init_db_command
from user import User
import requests
from oauthlib.oauth2 import WebApplicationClient

GOOGLE_CLIENT_ID = os.environ.get(
    "543251693947-uuomjheqpj6piup81pvbahrc3nu25o9m.apps.googleusercontent.com", None)
GOOGLE_CLIENT_SECRET = os.environ.get("T6BNa4xfhp3SeKRObBiw86tH", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass
client = WebApplicationClient(GOOGLE_CLIENT_ID)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()
# Flask-Login helper to retrieve a user from our db


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    client.parse_request_body_response(json.dumps(token_response.json()))
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
        user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture)
        if not User.get(unique_id):
            User.create(unique_id, users_name, users_email, picture)
            login_user(user)
            return redirect(url_for("index"))
    else:
        return "User email not available or not verified by Google.", 400

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return (
            "<p>Hello, {}! You're logged in! Email: {}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'.format(
                current_user.name, current_user.email, current_user.profile_pic
            )
        )
    else:
        # return render_template('login.html')
        return '<a class="button" href="/login">Google Login</a>'
# Mirar SQLAlchemy ORM


@app.route('/wallet')
def wallet():
    return render_template('tab1cartera.html', title='Cartera')


@app.route('/getcoins')
def getcoins():
    return render_template('tab2get.html')


@app.route('/offers')
def coins():
    return render_template('tab3offers.html')


# def login():
#     error =None
#     if request.method == 'POST':
#         if valid_login(request.form['username'], request.form['password']):
#             return log_the_user_in(request.form['username'])
#         else:
#             error = 'Invalid username or password'
#     return render_template('login.html', error=error)
if __name__ == "__main__":
    app.run(debug=True)

# if __name__ == "__main__":
#     app.run(ssl_context="adhoc")
