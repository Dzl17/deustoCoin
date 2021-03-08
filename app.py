from flask import Flask, url_for, render_template, request, redirect, Response, session, send_file
from authlib.integrations.flask_client import OAuth
from base import Session, init_db
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from models import User, Transaccion, Accion, Campanya, KPIporFechas
from datetime import datetime
from web3 import Web3
from forms import EnviarUDCForm, CrearCampForm, AccionesForm, CampanyasForm, ImageForm
import cryptocompare
import io
import ipfshttpclient
import qrcode
import os
import sys

# ropsten_url = Config.ROPSTEN_URL
# infura_secret = Config.INFURA_SECRET
# WEB3_INFURA_PROJECT_ID = Config.WEB3_INFURA_PROJECT_ID
# GOOGLE_DISCOVERY_URL = config.GOOGLE_DISCOVERY_URL


app = Flask(__name__)
app.config.from_object("config.Config")
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
app.config["SECRET_KEY"] = app.secret_key
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
test_address = app.config['TEST_ADDRESS']
private_key = app.config['PRIVATE_KEY']

web3 = Web3(Web3.HTTPProvider(app.config['ROPSTEN_URL']))
valorUDC = cryptocompare.get_price('ETH').get('ETH').get('EUR')
init_db()

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    # This is only needed if using openId to fetch user info
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
)


def get_balance(test_address):
    web3 = Web3(Web3.HTTPProvider(app.config['ROPSTEN_URL']))
    balance = web3.eth.getBalance(test_address)
    valorUDC = cryptocompare.get_price('ETH').get('ETH').get('EUR')
    balancefloat = float(web3.fromWei(balance, "ether")) * valorUDC
    print("Tu balance es de %.2f UDC" % balancefloat)
    return balancefloat


def sendCoins(dest, amount):
    destUser = User.get_by_email(dest)
    account_2 = destUser.blockHash
    print(account_2)
    print(private_key)
    nonce = web3.eth.getTransactionCount(test_address)
    accion = Accion.getActionById(session['accionId'])
    float_amount = float(amount) / valorUDC
    tx = {
        'nonce': nonce,
        'to': account_2,
        'value': web3.toWei(float_amount, 'ether'),
        'gas': 50000,
        'gasPrice': web3.toWei(100, 'gwei')  # gas: rapidez de transaccion
    }
    print("Funciona la transaccion desde aqui")
    signed_tx = web3.eth.account.signTransaction(tx, private_key)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    s = Session()
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%d-%m-%Y (%H:%M:%S.%f)")
    t = Transaccion(timestampStr, tx_hash, accion.empresa, dest, accion.campanya_id, amount)
    s.add(t)
    s.commit()
    query = s.query(Campanya)
    dictupdate = {Campanya.kpi: Campanya.kpi + (10 * accion.recompensa)}
    query.filter(Campanya.id == accion.campanya_id).update(dictupdate, synchronize_session=False)
    s.commit()
    s.close()


def create_figure(id):
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    data = KPIporFechas.getGraphData(id)
    titulo = data.get("name")
    axis.set_title("Valor de KPIs de la campaña " + titulo)
    axis.set_xlabel("Fecha")
    axis.set_ylabel("Valor del KPI")
    results = data.get("results")[::-1]
    xs = [x.fecha for x in results]
    print(xs)
    ys = [y.kpi for y in results]
    print(ys)
    axis.plot(xs, ys)
    return fig


@app.route('/')
def home():
    KPIporFechas.saveTodaysKPI()
    create_figure(1)
    return render_template("login.html")


@app.route('/login')
def login():
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    client = ipfshttpclient.connect(app.config['IPFS_CONNECT_URL'])
    file = request.files['filename']
    res = client.add(file)
    print(res)
    cReward = Accion.getActionById(session['accionId'])
    sendCoins(session['email'], cReward.recompensa)
    return render_template("recompensa.html", name=session['name'], accion=cReward, email=session['email'])


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
    user = User.get_by_email(session['email'])
    if 'accionId' in session and user != None:
        print(session['accionId'])
        print("Si hay acción para printear")
        cReward = Accion.getActionById(session['accionId'])
        # sendCoins(user_info['email'], cReward.recompensa)
        return render_template("subirimagen.html", name=session['name'], cReward=cReward, email=session['email'],
                               session=session, user=user, accionId=cReward)
    else:
        if user != None:
            if user.role == 'Profesor':
                return redirect('/wallet')
            if user.role == 'Promotor':
                return redirect('/accion')
                print("No hay acción")
            if user.role == 'Alumno':
                return redirect('/wallet')

        else:
            return redirect('/register')


@app.route('/register', methods=['GET', 'POST'])
def register():
    print(dict)
    email = dict(session).get('email', None)
    name = dict(session).get('name', None)
    picture = dict(session).get('picture', None)
    if request.method == "POST":
        nombre = request.form['nombre']
        email = request.form['email']
        blockchainAddr = request.form['blockAddr']
        session['blockchainAddr'] = blockchainAddr
        rol = request.form['rol']
        org = request.form['organizacion']

        s = Session()
        u = User(nombre, email, blockchainAddr, picture, rol, org)
        s.add(u)
        s.commit()
        if rol == 'Profesor':
            return redirect('/wallet')
        if rol == 'Promotor':
            return redirect('/accion')
    else:
        return render_template("register.html", email=email, nombre=name)


@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    form = EnviarUDCForm()
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    salary = get_balance(user.blockHash)
    if form.validate_on_submit():
        account_1 = user.blockHash
        destUser = User.get_by_email(request.form['destino'])
        account_2 = destUser.blockHash
        print(account_2)
        private_key = "e49aed1a79c5f2c703b5651dd09c840d3193175fd748fbea37e00ce8d83a3c7d"
        nonce = web3.eth.getTransactionCount(account_1)
        float_amount = float(request.form['cantidad']) / valorUDC
        tx = {
            'nonce': nonce,
            'to': account_2,
            'value': web3.toWei(float_amount, 'ether'),
            'gas': 50000,
            'gasPrice': web3.toWei(100, 'gwei')  # gas: rapidez de transaccion
        }
        signed_tx = web3.eth.account.signTransaction(tx, private_key)
        tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        s = Session()
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("%d-%b-%Y (%H:%M:%S.%f)")
        t = Transaccion(timestampStr, tx_hash, email, request.form['destino'], "Envío de UDC", request.form['cantidad'])
        s.add(t)
        s.commit()
    given_name = dict(session).get('given_name', None)
    name = dict(session).get('name', None)
    picture = dict(session).get('picture', None)
    transacciones = Transaccion.getTransactions(email)
    acciones = Accion.getAllActions()
    return render_template('tab1cartera.html', title='Cartera', wallet=salary, email=email, name=given_name, w3=web3,
                           form=form, picture=picture, user=user, transacciones=transacciones, acciones=acciones)


@app.route('/accion', methods=['GET', 'POST'])
def accion():
    form = CrearCampForm()
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    name = dict(session).get('name', None)
    picture = dict(session).get('picture', None)
    acciones = Accion.getActions(user.organizacion)
    campanyas = Campanya.getCampaigns(user.organizacion)
    salary = get_balance(user.blockHash)
    if form.validate_on_submit():
        s = Session()
        c = Campanya(request.form['nomCamp'], user.organizacion, request.form['desc'], 0)
        # print("objeto creado")
        s.add(c)
        s.commit()
    if request.method == 'POST' and 'crearAccion' in request.form:
        nombre = request.form['nombre']
        desc = request.form['desc']
        recompensa = request.form['recompensa']
        camp = request.form['campanya']
        s = Session()
        a = Accion(nombre, user.organizacion, desc, recompensa, camp)
        s.add(a)
        s.commit()
        intId = Accion.getIdByName(nombre)
        qr = qrcode.make(url_for("redeem", accion_id=intId, _external=True))
        qr.save('./static/qr/' + str(intId) + ".png")

    return render_template('accion.html', title='Acción', wallet=salary, email=email, name=given_name, w3=web3,
                           form=form, picture=picture, user=user, acciones=acciones, campanyas=campanyas)


@app.route('/accionalumnos', methods=['GET', 'POST'])
def accionalumnos():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    name = dict(session).get('name', None)
    salary = get_balance(user.blockHash)
    picture = dict(session).get('picture', None)
    acciones = Accion.getAllActions()
    return render_template('accionalumnos.html', title='Acción', wallet=salary, email=email, name=given_name, w3=web3,
                           picture=picture, user=user, acciones=acciones)


@app.route('/historialtrans', methods=['GET', 'POST'])
def historialtrans():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    salary = get_balance(user.blockHash)
    name = dict(session).get('name', None)
    picture = dict(session).get('picture', None)
    transacciones = Transaccion.getTransactions(user.email)
    for t in transacciones:
        campId = t.campanya
        t.campanya = Campanya.getCampaignById(campId).nombre
    return render_template('historialtrans.html', title='Acción', wallet=salary, email=email, name=name, w3=web3,
                           picture=picture, user=user, transacciones=transacciones)


@app.route('/editor/<int:campanya_id>', methods=['GET', 'POST'])
def editor(campanya_id):
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    name = dict(session).get('name', None)
    picture = dict(session).get('picture', None)
    acciones = Accion.getActionsOfCampaign(campanya_id)
    campanya = Campanya.getCampaignById(campanya_id)
    salary = get_balance(user.blockHash)
    s = Session()
    if request.method == 'POST':
        if 'editar' in request.form:
            return redirect(url_for('editorAccion', accion_id=request.form['id']))
        elif 'eliminar' in request.form:
            query = s.query(Accion)
            pk = request.form['id']
            query = query.filter(Accion.id == pk).first()
            s.delete(query)
            s.commit()
    return render_template('adminacciones.html', title='Acción', wallet=salary, email=email, name=given_name, w3=web3,
                           picture=picture, user=user, acciones=acciones, campanya=campanya)


@app.route('/plot<int:campanya_id>.png')
def plot_png(campanya_id):
    fig = create_figure(campanya_id)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')


@app.route('/editorC', methods=['GET', 'POST'])
def editorC():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    name = dict(session).get('name', None)
    picture = dict(session).get('picture', None)
    campanyas = Campanya.getCampaigns(user.organizacion)
    salary = get_balance(user.blockHash)
    s = Session()
    if request.method == 'POST':
        if 'editar' in request.form:
            return redirect(url_for('editorCamp', campanya_id=request.form['id']))
        elif 'eliminar' in request.form:
            query = s.query(Campanya)
            pk = request.form['id']
            query = query.filter(Campanya.id == pk).first()
            s.delete(query)
            s.commit()
        elif 'verAcc' in request.form:
            return redirect(url_for('editor', campanya_id=request.form['id']))
    return render_template('admincampanyas.html', title='Campañas', wallet=salary, email=email, name=given_name,
                           w3=web3, picture=picture, user=user, campanyas=campanyas)


@app.route('/editarAcc/<int:accion_id>', methods=["GET", "POST"])
def editorAccion(accion_id):
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    name = dict(session).get('name', None)
    picture = dict(session).get('picture', None)
    s = Session()
    query = s.query(Accion)
    accion = query.filter(Accion.id == accion_id).first()
    if request.method == 'POST':
        dictupdate = {Accion.nombre: request.form['nombre'], Accion.descripcion: request.form['descripcion'],
                      Accion.recompensa: float(request.form['recompensa'])}
        query.filter(Accion.id == accion_id).update(dictupdate, synchronize_session=False)
        s.commit()
    return render_template("editoraccion.html", accion=accion, email=email, name=given_name, picture=picture, user=user)


@app.route('/editorCampanyas/<int:campanya_id>', methods=["GET", "POST"])
def editorCamp(campanya_id):
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    name = dict(session).get('name', None)
    picture = dict(session).get('picture', None)
    user = User.get_by_email(email)

    s = Session()
    query = s.query(Campanya)
    campanya = query.filter(Campanya.id == campanya_id).first()
    if request.method == 'POST':
        dictupdate = {Campanya.nombre: request.form['nombre'], Campanya.descripcion: request.form['descripcion']}
        query.filter(Campanya.id == campanya_id).update(dictupdate, synchronize_session=False)
        s.commit()
    return render_template("editorcamp.html", campanya=campanya, email=email, name=given_name, picture=picture,
                           user=user)


@app.route('/qr/<int:accion_id>')
def qr(accion_id):
    path = 'static/qr/' + str(accion_id) + ".png"
    return send_file(path, as_attachment=True)


@app.route('/redeem/<int:accion_id>', methods=["GET", "POST"])
def redeem(accion_id):
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    session['accionId'] = accion_id
    return google.authorize_redirect(redirect_uri)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/campanyas')
def campanyas():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    name = dict(session).get('name', None)
    salary = get_balance(user.blockHash)
    picture = dict(session).get('picture', None)
    campanyas = Campanya.getOrderedCampaigns()
    empresas = Campanya.getDistinctCompanies()
    return render_template('empresas.html', wallet=salary, email=email, name=given_name, w3=web3, picture=picture,
                           user=user, campanyas=campanyas, empresas=empresas)


@app.route('/campanyas/<emp>', methods=['GET', 'POST'])
def empresa(emp):
    print(emp)
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    name = dict(session).get('name', None)
    salary = get_balance(user.blockHash)
    picture = dict(session).get('picture', None)
    campanyas = Campanya.getCampaigns(emp)
    return render_template('campanyas.html', wallet=salary, email=email, name=given_name, w3=web3, picture=picture,
                           user=user, campanyas=campanyas, empresa=emp)


if __name__ == "__main__":
    app.run()
