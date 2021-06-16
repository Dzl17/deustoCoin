from flask import Flask, url_for, render_template, request, redirect, Response, session, \
    send_from_directory, make_response
from flask_babel import Babel, gettext
from authlib.integrations.flask_client import OAuth
from base import Session, init_db
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from models import User, Transaccion, Accion, Campanya, KPIporFechas, Oferta
from datetime import datetime
from web3 import Web3
from forms import EnviarUDCForm, CrearCampForm, CrearOfertaForm
from googletrans import Translator
from flask.cli import with_appcontext
import cryptocompare
import io
import ipfshttpclient
import matplotlib.pyplot as plt
import pytest
import qrcode
import os

app = Flask(__name__)
babel = Babel(app)
translator = Translator()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
test_address = os.environ.get('TEST_ADDRESS')
private_key = os.environ.get('PRIVATE_KEY')
web3 = Web3(Web3.HTTPProvider(os.environ.get('ROPSTEN_URL')))
valorUDC = cryptocompare.get_price('ETH').get('ETH').get('EUR')
init_db()
app.secret_key = os.environ.get("PRIVATE_KEY")
app.config["PRIVATE_KEY"] = app.secret_key

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
)


@babel.localeselector
def get_locale():
    if request.args.get('lang'):
        session['lang'] = request.args.get('lang')
    return session.get('lang', request.accept_languages.best_match(['en', 'es', 'eu']))


@app.cli.command()
@with_appcontext
def init():
    init_db()


def get_balance(test_address):
    web3 = Web3(Web3.HTTPProvider(os.environ.get('ROPSTEN_URL')))
    balance = web3.eth.getBalance(test_address)
    valorUDC = cryptocompare.get_price('ETH').get('ETH').get('EUR')
    balancefloat = float(web3.fromWei(balance, "ether")) * valorUDC
    return balancefloat


def sendCoins(dest, amount, imgHash, urlProof):
    destUser = User.get_by_email(dest)
    account_2 = destUser.blockHash

    nonce = web3.eth.getTransactionCount(test_address)

    accion = Accion.getActionById(session['accionId'])
    float_amount = float(amount) / valorUDC
    bytesStr = "acc:" + accion.nombre + " img: " + imgHash
    tx = {
        'chainId': 3,  # es 3 para Ropsten
        'nonce': nonce,
        'to': account_2,
        'value': web3.toWei(float_amount, 'ether'),
        'gas': 50000,
        'gasPrice': web3.toWei(50, 'gwei'),
        'data': bytes(bytesStr, 'utf8')
    }
    signed_tx = web3.eth.account.signTransaction(tx, private_key)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    s = Session()
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%d-%m-%Y (%H:%M:%S.%f)")
    t = Transaccion(timestampStr, tx_hash, accion.empresa, dest, accion.campanya_id, amount, imgHash, urlProof)
    s.add(t)
    s.commit()
    query = s.query(Accion)
    kpi = int(float(request.form['kpi']))
    dictupdate = {Accion.kpi: Accion.kpi + kpi}
    query.filter(Accion.id == accion.id).update(dictupdate, synchronize_session=False)
    s.commit()
    s.close()


def offerTransaction(rem, dest, offer):
    destUser = User.get_by_email(dest)
    account_2 = destUser.blockHash
    remUser = User.get_by_email(rem)
    nonce = web3.eth.getTransactionCount(remUser.blockHash)
    amount = offer.precio
    strOffer = "Pago por oferta: " + offer.nombre
    float_amount = float(amount) / valorUDC
    tx = {
        'chainId': 3,  # es 3 para Ropsten
        'nonce': nonce,
        'to': account_2,
        'value': web3.toWei(float_amount, 'ether'),
        'gas': 50000,
        'gasPrice': web3.toWei(50, 'gwei'),
        'data': bytes(strOffer, 'utf8')

    }
    signed_tx = web3.eth.account.signTransaction(tx, remUser.pk)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    s = Session()
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%d-%m-%Y (%H:%M:%S.%f)")
    t = Transaccion(timestampStr, tx_hash, rem, destUser.organizacion, None, amount, "", "")
    s.add(t)
    s.commit()
    s.close()


def create_figure(id):
    try:
        fig = Figure()
        axis = fig.add_subplot(1, 1, 1)
        accion = Accion.getActionById(id)
        data = KPIporFechas.getGraphData(id)
        titulo = data.get("name")
        axis.set_title(titulo + " - " + accion.indicadorKpi)
        axis.set_ylim(0, accion.kpiObj)
        stringFecha = "Fecha"
        try:
            stringFecha = translator.translate(stringFecha, dest=session['lang']).text
            accion.indicadorKpi = translator.translate(accion.indicadorKpi, dest=session['lang']).text
        except:
            pass
        axis.set_xlabel(stringFecha)
        axis.set_ylabel(accion.indicadorKpi)
        results = data.get("results")[::-1]
        xs = [x.fecha for x in results]
        ys = [y.kpi for y in results]
        print(xs)
        axis.plot(xs, ys)
        print(type(axis))
        return fig
    except:
        return None


@app.route('/')
def home():
    KPIporFechas.saveTodaysKPI()
    return render_template("index.html")


@app.route('/language/<lang>')
def language(lang):
    session['lang'] = lang
    return redirect(request.referrer)


@app.route('/login')
def login():
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    client = ipfshttpclient.connect(os.environ.get('IPFS_CONNECT_URL'))
    user = User.get_by_email(session['email'])
    try:
        urlProof = request.form['proof']
    except:
        urlProof = ""
    file = request.files['filename']
    res = client.add(file)
    client.close()
    cReward = Accion.getActionById(session['accionId'])
    kpi = request.form['kpi']
    strRecompensa = str(cReward.recompensa).replace(",", ".")
    cReward.recompensa = float(strRecompensa) * float(kpi)
    sendCoins(session['email'], cReward.recompensa, res['Hash'], urlProof)
    try:
        cReward.nombre = translator.translate(cReward.nombre, dest=session['lang']).text
    except:
        pass
    del session['accionId']
    return render_template("recompensa.html", name=session['name'], accion=cReward, email=session['email'], user=user)


@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    session['email'] = user_info['email']
    session['given_name'] = user_info['given_name']
    session['name'] = user_info['name']
    session['picture'] = user_info['picture']
    session['token'] = token
    user = User.get_by_email(session['email'])

    if 'accionId' in session and user is not None:
        cReward = Accion.getActionById(session['accionId'])
        try:
            cReward.nombre = translator.translate(cReward.nombre, dest=session['lang']).text
            cReward.descripcion = translator.translate(cReward.descripcion, dest=session['lang']).text
            cReward.indicadorKpi = translator.translate(cReward.indicadorKpi, dest=session['lang']).text
        except:
            pass
        if cReward is not None:
            return render_template("subirimagen.html", name=session['name'], cReward=cReward, email=session['email'],
                                   session=session, user=user, accionId=cReward)
        else:
            return redirect('/wallet')
    if 'offerId' in session and user is not None:
        offer = Oferta.getOfferById(session['offerId'])
        if offer is not None:
            dest = User.getCompanyBlockAddr(offer.empresa).email
            offerTransaction(session['email'], dest, offer)
            try:
                offer.nombre = translator.translate(offer.nombre, dest=session['lang']).text
            except:
                pass
            return render_template("pago.html", name=session['name'], offer=offer, email=session['email'],
                                   session=session, user=user)
        else:
            return redirect('/wallet')
    else:
        if user is not None:
            if user.role == 'Colaborador':
                return redirect('/wallet')
            else:
                return redirect('/accion')

        else:
            return redirect('/register')


@app.route('/register', methods=['GET', 'POST'])
def register():
    email = dict(session).get('email', None)
    name = dict(session).get('name', None)
    picture = dict(session).get('picture', None)
    if request.method == "POST":
        nombre = request.form['nombre']
        email = request.form['email']
        blockchainAddr = request.form['blockAddr']
        session['blockchainAddr'] = blockchainAddr
        pk = request.form['pk']
        rol = request.form['rol']
        org = request.form['organizacion']

        s = Session()
        u = User(nombre, email, blockchainAddr, pk, picture, rol, org)
        s.add(u)
        s.commit()
        if rol == 'Colaborador':
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
        nonce = web3.eth.getTransactionCount(account_1)
        float_amount = float(request.form['cantidad']) / valorUDC
        tx = {
            'chainId': 3,
            'nonce': nonce,
            'to': account_2,
            'value': web3.toWei(float_amount, 'ether'),
            'gas': 50000,
            'gasPrice': web3.toWei(100, 'gwei')
        }
        signed_tx = web3.eth.account.signTransaction(tx, user.pk)
        tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        s = Session()
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("%d-%b-%Y (%H:%M:%S.%f)")
        t = Transaccion(timestampStr, tx_hash, email, request.form['destino'], None, request.form['cantidad'], "", "")
        s.add(t)
        s.commit()
    given_name = dict(session).get('given_name', None)
    try:
        del session['accionId']
        del session['offerId']
    except:
        pass
    return render_template('tab1cartera.html', title='Cartera', wallet=salary, email=email, name=given_name, w3=web3,
                           form=form, user=user)


@app.route('/redeemOffer/<int:offer_id>')
def redeemOffer(offer_id):
    offer = Oferta.getOfferById(offer_id)
    user = User.get_by_email(session['email'])
    dest = User.getCompanyBlockAddr(offer.empresa).email
    offerTransaction(session['email'], dest, offer)
    try:
        offer.nombre = translator.translate(offer.nombre, dest=session['lang']).text
    except:
        pass
    return render_template("pago.html", name=session['name'], offer=offer, email=session['email'],
                           session=session, user=user)


@app.route('/accion', methods=['GET', 'POST'])
def accion():
    form = CrearCampForm()
    form2 = CrearOfertaForm()
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)

    if user.role == "Promotor":
        campanyas = Campanya.getCampaigns(user.organizacion)
        acciones = Accion.getActions(user.organizacion)
        ofertas = Oferta.getOffers(user.organizacion)
    elif user.role == "Administrador":
        campanyas = Campanya.getAllCampaigns()
        acciones = Accion.getAllActions()
        ofertas = Oferta.getAllOffers()
    else:
        return redirect("/login")
    try:
        for c in campanyas:
            c.nombre = translator.translate(c.nombre, dest=session['lang']).text
            c.descripcion = translator.translate(c.descripcion, dest=session['lang']).text
        for a in acciones:
            a.nombre = translator.translate(a.nombre, dest=session['lang']).text
            a.descripcion = translator.translate(a.descripcion, dest=session['lang']).text
            a.indicadorKpi = translator.translate(a.indicadorKpi, dest=session['lang']).text
        for o in ofertas:
            o.nombre = translator.translate(o.nombre, dest=session['lang']).text
            o.descripcion = translator.translate(o.descripcion, dest=session['lang']).text
    except:
        pass
    salary = get_balance(os.environ.get('TEST_ADDRESS'))
    if form.validate_on_submit() and form.crearCamp.data:
        s = Session()
        if user.role == "Promotor":
            c = Campanya(request.form['nomCamp'], user.organizacion, request.form['desc'])
        elif user.role == "Administrador":
            c = Campanya(request.form['nomCamp'], request.form['empresa'], request.form['desc'])
        s.add(c)
        s.commit()
    elif form2.validate_on_submit() and form2.crearOf.data:
        nombre = request.form['nomOferta']
        s = Session()
        if user.role == "Promotor":
            o = Oferta(request.form['nomOferta'], user.organizacion, request.form['desc'], request.form['precio'])
        elif user.role == "Administrador":
            o = Oferta(request.form['nomOferta'], request.form['empresa'], request.form['desc'], request.form['precio'])
        s.add(o)
        s.commit()

    if request.method == 'POST' and 'crearAccion' in request.form:
        nombre = request.form['nombre']
        desc = request.form['desc']
        recompensa = request.form['recompensa']
        indKpi = request.form['kpi']
        kpiObj = request.form['obj']
        camp = request.form['campanya']
        s = Session()
        a = Accion(nombre, user.organizacion, desc, recompensa, indKpi, kpiObj, camp)
        s.add(a)
        s.commit()

    try:
        del session['accionId']
        del session['offerId']
    except:
        pass
    # Borro las keys para evitar conflictos con cookies
    return render_template('accion.html', title='Acción', wallet=salary, email=email, name=given_name, w3=web3,
                           form=form, form2=form2, user=user, acciones=acciones, campanyas=campanyas, ofertas=ofertas)


@app.route('/accionalumnos', methods=['GET', 'POST'])
def accionalumnos():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    salary = get_balance(user.blockHash)
    acciones = Accion.getAllActions()
    try:
        for a in acciones:
            a.nombre = translator.translate(a.nombre, dest=session['lang']).text
            a.descripcion = translator.translate(a.descripcion, dest=session['lang']).text
    except:
        pass
    try:
        del session['accionId']
        del session['offerId']
    except:
        pass
    return render_template('accionalumnos.html', title='Acción', wallet=salary, email=email, name=given_name, w3=web3,
                           user=user, acciones=acciones)


@app.route('/ofertas', methods=['GET', 'POST'])
def ofertas():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    salary = get_balance(user.blockHash)
    ofertas = Oferta.getAllOffers()
    try:
        for o in ofertas:
            o.nombre = translator.translate(o.nombre, dest=session['lang']).text
            o.descripcion = translator.translate(o.descripcion, dest=session['lang']).text
    except:
        pass
    try:
        del session['accionId']
        del session['offerId']
    except:
        pass
    return render_template('ofertas.html', title='Oferta', wallet=salary, email=email, name=given_name, w3=web3,
                           user=user, ofertas=ofertas)


@app.route('/historialtrans', methods=['GET', 'POST'])
def historialtrans():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    salary = get_balance(user.blockHash)
    name = dict(session).get('name', None)

    if user.role == "Colaborador":
        transacciones = Transaccion.getTransactions(user.email)
    elif user.role == "Promotor":
        transacciones = Transaccion.getTransactions(user.organizacion)
    else:
        transacciones = Transaccion.getAllTransactions()
    for t in transacciones:
        campId = t.campanya
        try:
            t.campanya = Campanya.getCampaignById(campId).nombre
            try:
                t.campanya = translator.translate(t.campanya, dest=session['lang']).text
            except:
                pass
        except:
            if "@" not in str(t.destinatario):
                t.campanya = gettext("Pago por oferta")
            else:
                t.campanya = gettext("Envío de UDCoins")

    try:
        del session['accionId']
        del session['offerId']
    except:
        pass
    return render_template('historialtrans.html', title='Acción', wallet=salary, email=email, name=name, w3=web3,
                           user=user, transacciones=transacciones)


@app.route('/editor/<int:campanya_id>', methods=['GET', 'POST'])
def editor(campanya_id):
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    acciones = Accion.getActionsOfCampaign(campanya_id)
    campanya = Campanya.getCampaignById(campanya_id)
    salary = get_balance(user.blockHash)
    s = Session()
    if request.method == 'POST':
        if 'editarAcc' in request.form:
            return redirect(url_for('editorAccion', accion_id=request.form['accion_id']))
        elif 'eliminarAcc' in request.form:
            query = s.query(Accion)
            pk = request.form['accion_id']
            query = query.filter(Accion.id == pk).first()
            s.delete(query)
            s.commit()
            acciones = Accion.getActionsOfCampaign(campanya_id)

    return render_template('adminacciones.html', title='Acción', wallet=salary, email=email, name=given_name, w3=web3,
                           user=user, acciones=acciones, campanya=campanya)


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
    if user.role == "Promotor":
        campanyas = Campanya.getCampaigns(user.organizacion)
    if user.role == "Administrador":
        campanyas = Campanya.getAllCampaigns()
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
    try:
        del session['accionId']
        del session['offerId']
    except:
        pass
    return render_template('admincampanyas.html', title='Campañas', wallet=salary, email=email, name=given_name,
                           w3=web3, user=user, campanyas=campanyas)


@app.route('/editorO', methods=['GET', 'POST'])
def editorO():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    if user.role == "Promotor":
        ofertas = Oferta.getOffers(user.organizacion)
    if user.role == "Administrador":
        ofertas = Oferta.getAllOffers()
    salary = get_balance(user.blockHash)
    s = Session()
    if request.method == 'POST':
        if 'editarO' in request.form:
            return redirect(url_for('editorOferta', offer_id=request.form['id']))
        elif 'eliminarO' in request.form:
            query = s.query(Oferta)
            pk = request.form['id']
            query = query.filter(Oferta.id == pk).first()
            s.delete(query)
            s.commit()
            if user.role == "Promotor":
                ofertas = Oferta.getOffers(user.organizacion)
            if user.role == "Administrador":
                ofertas = Oferta.getAllOffers()
    try:
        del session['accionId']
        del session['offerId']
    except:
        pass
    return render_template('adminofertas.html', title='Ofertas', wallet=salary, email=email, name=given_name,
                           w3=web3, user=user, ofertas=ofertas)


@app.route('/editarAcc/<int:accion_id>', methods=["GET", "POST"])
def editorAccion(accion_id):
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    s = Session()
    query = s.query(Accion)
    accion = query.filter(Accion.id == accion_id).first()
    if request.method == 'POST' and 'actualizarA' in request.form:
        dictupdate = {Accion.nombre: request.form['nombre'], Accion.descripcion: request.form['descripcion'],
                      Accion.recompensa: float(request.form['recompensa']),
                      Accion.indicadorKpi: request.form['indicadorKpi'], Accion.kpiObj: int(request.form['kpiObj'])}
        query.filter(Accion.id == accion_id).update(dictupdate, synchronize_session=False)
        s.commit()
    return render_template("editoraccion.html", accion=accion, email=email, name=given_name, user=user)


@app.route('/editorCampanyas/<int:campanya_id>', methods=["GET", "POST"])
def editorCamp(campanya_id):
    email = dict(session).get('email', None)
    given_name = dict(session).get('given_name', None)
    user = User.get_by_email(email)

    s = Session()
    query = s.query(Campanya)
    campanya = query.filter(Campanya.id == campanya_id).first()
    if request.method == 'POST':
        dictupdate = {Campanya.nombre: request.form['nombre'], Campanya.descripcion: request.form['descripcion']}
        query.filter(Campanya.id == campanya_id).update(dictupdate, synchronize_session=False)
        s.commit()
    return render_template("editorcamp.html", campanya=campanya, email=email, name=given_name,
                           user=user)


@app.route('/editorOferta/<int:offer_id>', methods=["GET", "POST"])
def editorOferta(offer_id):
    email = dict(session).get('email', None)
    given_name = dict(session).get('given_name', None)
    user = User.get_by_email(email)

    s = Session()
    query = s.query(Oferta)
    oferta = query.filter(Oferta.id == offer_id).first()
    if request.method == 'POST':
        dictupdate = {Oferta.nombre: request.form['nombre'], Oferta.descripcion: request.form['descripcion'],
                      Oferta.precio: request.form['precio']}
        query.filter(Oferta.id == offer_id).update(dictupdate, synchronize_session=False)
        s.commit()
    return render_template("editoroferta.html", oferta=oferta, email=email, name=given_name,
                           user=user)


@app.route('/qr/<int:accion_id>')
def qr(accion_id):
    img = qrcode.make(url_for("redeem", accion_id=accion_id, _external=True))
    with io.BytesIO() as output:
        img.save(output, format="PNG")
        contents = output.getvalue()
    return Response(contents, mimetype='image/png')


@app.route('/qrOfertas/<int:offerId>')
def qrOfertas(offerId):
    img = qrcode.make(url_for("pay", offer_id=offerId, _external=True))
    with io.BytesIO() as output:
        img.save(output, format="PNG")
        contents = output.getvalue()
    return Response(contents, mimetype='image/png')


@app.route('/redeem/<int:accion_id>', methods=["GET", "POST"])
def redeem(accion_id):
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    session['accionId'] = accion_id
    return google.authorize_redirect(redirect_uri)


@app.route('/pay/<int:offer_id>', methods=["GET", "POST"])
def pay(offer_id):
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    session['offerId'] = offer_id
    return google.authorize_redirect(redirect_uri)


@app.route('/logout')
def logout():
    try:
        tempLang = session['lang']
        session.clear()
        session['lang'] = tempLang
    except:
        pass
    return redirect('/')


@app.route('/sobre')
def sobre():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    try:
        del session['accionId']
        del session['offerId']
    except:
        pass
    return render_template('sobre.html', email=email, name=given_name,
                           user=user)


@app.route('/campanyas')
def campanyas():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    campanyas = Campanya.getOrderedCampaigns()
    empresas = Campanya.getDistinctCompanies()
    try:
        for c in campanyas:
            c.nombre = translator.translate(c.nombre, dest=session['lang']).text
            c.descripcion = translator.translate(c.descripcion, dest=session['lang']).text

    except:
        pass
    try:
        del session['accionId']
        del session['offerId']
    except:
        pass
    return render_template('empresas.html', email=email, name=given_name,
                           user=user, campanyas=campanyas, empresas=empresas)


@app.route('/campanyas/<emp>', methods=['GET', 'POST'])
def empresa(emp):
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    salary = get_balance(user.blockHash)
    campanyas = Campanya.getCampaigns(emp)
    acciones = Accion.getActions(emp)
    try:
        for c in campanyas:
            c.nombre = translator.translate(c.nombre, dest=session['lang']).text
            c.descripcion = translator.translate(c.descripcion, dest=session['lang']).text
        for a in acciones:
            a.nombre = translator.translate(a.nombre, dest=session['lang']).text
            a.descripcion = translator.translate(a.descripcion, dest=session['lang']).text
    except:
        pass
    return render_template('campanyas.html', wallet=salary, email=email, name=given_name, w3=web3,
                           user=user, campanyas=campanyas, empresa=emp, acciones=acciones)


@app.route('/registraraccion/<int:accion_id>', methods=['GET', 'POST'])
def registrarAccion(accion_id):
    user = User.get_by_email(session['email'])
    session['accionId'] = accion_id
    cReward = Accion.getActionById(accion_id)
    try:
        cReward.nombre = translator.translate(cReward.nombre, dest=session['lang']).text
        cReward.descripcion = translator.translate(cReward.descripcion, dest=session['lang']).text
        cReward.indicadorKpi = translator.translate(cReward.indicadorKpi, dest=session['lang']).text
    except:
        pass
    return render_template("subirimagen.html", name=session['name'], cReward=cReward, email=session['email'],
                           session=session, user=user, accionId=accion_id)


@app.route('/sw.js')
def sw():
    response = make_response(send_from_directory('static', filename='sw.js'))
    response.headers['Content-Type'] = 'application/javascript'
    return response


@app.before_request
def before_request():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)


@app.errorhandler(500)
def internal_error(e):
    return render_template("error.html", code="500", type="Internal Server Error"), 500


@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code="403", type="Forbidden"), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", code="404", type="Not Found"), 404


@app.errorhandler(400)
def bad_request(e):
    return render_template("error.html", code="400", type="Bad Request"), 400


@app.errorhandler(401)
def unauthorized(e):
    return render_template("error.html", code="401", type="Unauthorized"), 401


if __name__ == "__main__":
    app.run()
