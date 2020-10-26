from flask import Flask, url_for, render_template, request, redirect, session
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from authlib.integrations.flask_client import OAuth
import json
import os
import sys
import sqlite3
from db import init_db_command
from user import User
import requests
from oauthlib.oauth2 import WebApplicationClient
from flask_restful import Resource, Api
from web3.auto import w3;

# GOOGLE_CLIENT_ID = os.environ.get(
#     "543251693947-uuomjheqpj6piup81pvbahrc3nu25o9m.apps.googleusercontent.com", None)
# GOOGLE_CLIENT_SECRET = os.environ.get("T6BNa4xfhp3SeKRObBiw86tH", None)
# GOOGLE_DISCOVERY_URL = (
#     "https://accounts.google.com/.well-known/openid-configuration"
# )

infura_url = "https://ropsten.infura.io/v3/834fad9971d14e4cb81715ed0f7adb0a"
infura_secret = "0bc36d15c0a841b7835509d9b9fd0f52"
ropsten_url = "https://ropsten.etherscan.io/address/0x99ad62313b591405ba1c51aa50294245a36f1289"
WEB3_INFURA_PROJECT_ID="834fad9971d14e4cb81715ed0f7adb0a"
GOOGLE_CLIENT_ID = "543251693947-uuomjheqpj6piup81pvbahrc3nu25o9m.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "60ajlp1BRZMnryrOBFD1sMkz"
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
test_address = "0x99AD62313b591405Ba1C51aa50294245A36F1289"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)


api = Api(app) 
# web3 = Web3(Web3.HTTPProvider(ropsten_url))
# balance = web3.eth.getBalance(test_address)
# int_balance = web3.fromWei(balance, "ether")
# print("Tu balance es de ", web3.fromWei(balance, "ether"))
#Configurando OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='543251693947-uuomjheqpj6piup81pvbahrc3nu25o9m.apps.googleusercontent.com',
    client_secret='60ajlp1BRZMnryrOBFD1sMkz',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
)

@app.route('/')
def hello_world():
    email = dict(session).get('token', None)
    return f"Tu balance es de {int_balance}"

@app.route('/login')
def login():
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')
    token = google.authorize_access_token()

    resp = google.get('userinfo')
    user_info = resp.json()
    print((dict(user_info)), file=sys.stderr)
    session['email'] = user_info['email']
    session['token'] = token

    return redirect('/')

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
