from flask import Flask, url_for, render_template, request, redirect, session
# from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
import os
import sys
import sqlite3
from base import Base, Session, init_db
from models import User
import requests
from oauthlib.oauth2 import WebApplicationClient
from flask_restful import Resource, Api
from web3 import Web3
import json
from forms import EnviarUDCForm
# import pymongo
# from pymongo import MongoClient

# GOOGLE_CLIENT_ID = os.environ.get(
#     "543251693947-uuomjheqpj6piup81pvbahrc3nu25o9m.apps.googleusercontent.com", None)
# GOOGLE_CLIENT_SECRET = os.environ.get("T6BNa4xfhp3SeKRObBiw86tH", None)
# GOOGLE_DISCOVERY_URL = (
#     "https://accounts.google.com/.well-known/openid-configuration"
# )

# cluster = MongoClient("mongodb+srv://root:root@cluster0.aaqli.mongodb.net/DeustoCoin?retryWrites=true&w=majority")
# db = cluster["deustoCoin"]
# collection = db["deustoCoin"]

ropsten_url = "https://ropsten.infura.io/v3/834fad9971d14e4cb81715ed0f7adb0a"
infura_secret = "0bc36d15c0a841b7835509d9b9fd0f52"
WEB3_INFURA_PROJECT_ID = "834fad9971d14e4cb81715ed0f7adb0a"
GOOGLE_CLIENT_ID = "543251693947-uuomjheqpj6piup81pvbahrc3nu25o9m.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "60ajlp1BRZMnryrOBFD1sMkz"
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
test_address = "0x99AD62313b591405Ba1C51aa50294245A36F1289"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
app.config["SECRET_KEY"] = app.secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:root@localhost:5432/deustoCoin'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# login_manager = LoginManager(app)
# login_manager.login_view = "login"
# db = SQLAlchemy(app)

api = Api(app)
web3 = Web3(Web3.HTTPProvider(ropsten_url))
balance = web3.eth.getBalance(test_address)
int_balance = web3.fromWei(balance, "ether")
init_db()
str_abi = '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"INITIAL_SUPPLY","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_value","type":"uint256"}],"name":"burn","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_value","type":"uint256"}],"name":"burnFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"inputs":[{"name":"_name","type":"string"},{"name":"_symbol","type":"string"},{"name":"_decimals","type":"uint256"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_burner","type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Burn","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"owner","type":"address"},{"indexed":true,"name":"spender","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"from","type":"address"},{"indexed":true,"name":"to","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Transfer","type":"event"}]'
abi = json.loads(str_abi)
address = "0x4BFBa4a8F28755Cb2061c413459EE562c6B9c51b"  # OMG Network
contract = web3.eth.contract(address=address, abi=abi)
totalSupply = contract.functions.totalSupply().call()
destname = contract.functions.name().call()
destsymbol = contract.functions.symbol().call()


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
    # This is only needed if using openId to fetch user info
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
)


# @app.route('/enviarUDC', method = 'POST')
# def sendUDC():
#     account_1 = "0x99AD62313b591405Ba1C51aa50294245A36F1289"
#     account_2 = "0x52351E33B3C693cc05f21831647EBdAb8a68Eb95"

#     private_key = "e49aed1a79c5f2c703b5651dd09c840d3193175fd748fbea37e00ce8d83a3c7d"
#     nonce = web3.eth.getTransactionCount(account_1)


#     tx = {
#         'nonce': nonce,
#         'to': account_2,
#         'value': web3.toWei(0.5, 'ether'),
#         'gas': 2000000,
#         'gasPrice': web3.toWei('50', 'gwei') //gas: rapidez de transaccion
#     }
#     signed_tx = web3.eth.account.signTransaction(tx, private_key)
#     tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
#     print(tx_hash)


@app.route('/')
def home():
    return render_template("login.html")


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
    session['given_name'] = user_info['given_name']
    session['name'] = user_info['name']
    session['picture'] = user_info['picture']

    session['token'] = token
    user = User.get_by_email(user_info['email'])
    if user != None:
        return redirect('/wallet')
    else:
        return redirect('/register')
    #return redirect('/wallet')

@app.route('/register', methods=['GET', 'POST'])
def register():
    print(dict)
    email = dict(session).get('email', None)
    name = dict(session).get('name', None)
    picture = dict(session).get('picture', None)
    if request.method == "POST":
        print("postttt")
        nombre = request.form['nombre'] 
        email = request.form['email']
        blockchainAddr = request.form['email']
        rol = request.form['rol']
        s = Session()
        u = User(nombre, email, blockchainAddr, rol)
        s.add(u)
        s.commit()
        s.close()
        print(u)
    else:
        print("no pilla el post")
    return render_template("register.html", email = email, nombre = name)

@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    form = EnviarUDCForm()
    if form.validate_on_submit():
        account_1 = "0x99AD62313b591405Ba1C51aa50294245A36F1289"
        account_2 = request.form['destino']

        private_key = "e49aed1a79c5f2c703b5651dd09c840d3193175fd748fbea37e00ce8d83a3c7d"
        nonce = web3.eth.getTransactionCount(account_1)
        float_amount = float(request.form['cantidad'])/1000
        tx = {
            'nonce': nonce,
            'to': account_2,
            'value': web3.toWei(float_amount, 'ether'),
            'gas': 50000,
            'gasPrice': web3.toWei(100, 'gwei') #gas: rapidez de transaccion
        }
        signed_tx = web3.eth.account.signTransaction(tx, private_key)
        tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        print(tx_hash)
    else:
        print("form no submitteado")
    email = dict(session).get('email', None)
    given_name = dict(session).get('given_name', None)
    name = dict(session).get('name', None)
    return render_template('tab1cartera.html', title='Cartera', wallet=int_balance, email=email, name=given_name, w3=web3, form = form)


@app.route('/getcoins')
def getcoins():
    return render_template('tab2get.html')


@app.route('/offers')
def offers():
    return render_template('tab3offers.html')


# @app.route('/logout')
# def logout():
#     logouturl = "https://appengine.google.com/_ah/logout?continue=" + "localhost:5000"
#     return redirect(logouturl)


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
