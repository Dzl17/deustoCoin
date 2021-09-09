from flask import Flask, url_for, render_template, request, redirect, Response, session, \
    send_from_directory, make_response
from flask_babel import Babel, gettext
from authlib.integrations.flask_client import OAuth
from base import Session, init_db
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from models import User, Transaccion, Accion, Campanya, KPIporFechas, Oferta
from datetime import datetime, time
from forms import SendUDCForm, CreateCampaignForm, CreateOfferForm
from googletrans import Translator
from flask.cli import with_appcontext
from contracts import *
import io
import ipfshttpclient
import qrcode
import os
import requests
import time

admin_address = os.environ.get('ADMIN_ADDRESS')
private_key = os.environ.get('PRIVATE_KEY')
blockchain_manager = BlockchainManager()

app = Flask(__name__)
app.secret_key = private_key
app.config['PRIVATE_KEY'] = private_key
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
babel = Babel(app)
translator = Translator()
init_db()

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


def get_balance(address):
    """Return the balance of the parameter address."""
    return blockchain_manager.balance_of(address=address)/100    # Divide to create equivalence to the Euro


def reward_coins(dest, promoter_address, action_id, amount, img_hash, url_proof):
    """Reward the input amount of coins to the user that completes a good deed."""
    dest_user = User.get_by_email(dest)
    dest_address = dest_user.blockHash
    accion = Accion.get_action_by_id(session['accionId'])

    tx_hash = blockchain_manager.transfer(caller=admin_address, callerKey=private_key, to=dest_address, value=int(float(amount)*100))
    blockchain_manager.emit_action(caller=admin_address, callerKey=private_key, promoter=promoter_address, to=dest_address, actionID=action_id, reward=amount, time=int(time.time()), ipfs_hash=img_hash, proof_url=url_proof)

    s = Session()
    datetime_obj = datetime.now()
    timestamp_str = datetime_obj.strftime("%d-%m-%Y (%H:%M:%S.%f)")
    t = Transaccion(timestamp_str, tx_hash, accion.empresa, dest, accion.campanya_id, amount, img_hash, url_proof)
    s.add(t)
    s.commit()
    query = s.query(Accion)
    kpi = int(float(request.form['kpi']))   # TODO: what is this
    dictupdate = {Accion.kpi: Accion.kpi + kpi}
    query.filter(Accion.id == accion.id).update(dictupdate, synchronize_session=False)
    s.commit()
    s.close()


def offer_transaction(rem, dest, offer):
    """Pay to a company in exchange for an offer."""
    dest_user = User.get_by_email(dest)
    dest_address = dest_user.blockHash
    rem_user = User.get_by_email(rem)
    rem_address = rem_user.blockHash
    rem_key = rem_user.pk
    value = int(float(offer.precio)*100)

    tx_hash = blockchain_manager.transfer(caller=rem_address, callerKey=rem_key, to=dest_address, value=value)

    s = Session()
    datetime_obj = datetime.now()
    timestamp_str = datetime_obj.strftime("%d-%m-%Y (%H:%M:%S.%f)")
    t = Transaccion(timestamp_str, tx_hash, rem, dest_user.organizacion, None, offer.precio, "", "")
    s.add(t)
    s.commit()
    s.close()


def transfer_coins(rem, dest, amount, email, dest_email):
    """Transfer coins to another user."""
    owner_address = rem.blockHash
    dest_address = dest.blockHash
    value=int(float(amount)*100)

    tx_hash = blockchain_manager.transfer(caller=owner_address, callerKey=rem.pk, to=dest_address, value=value)

    s = Session()
    datetime_obj = datetime.now()
    timestamp_str = datetime_obj.strftime("%d-%b-%Y (%H:%M:%S.%f)")
    t = Transaccion(timestamp_str, tx_hash, email, dest_email, None, amount, "", "")
    s.add(t)
    s.commit()


def create_figure(id):
    """Generates a Matplotlib visualization of a given action."""
    try:
        fig = Figure()
        axis = fig.add_subplot(1, 1, 1)
        accion = Accion.get_action_by_id(id)
        data = KPIporFechas.get_graph_data(id)
        titulo = data.get("name")
        axis.set_title(titulo + " - " + accion.indicadorKpi)
        axis.set_ylim(0, accion.kpiObj)
        string_fecha = "Fecha"
        try:
            string_fecha = translator.translate(string_fecha, dest=session['lang']).text
            accion.indicadorKpi = translator.translate(accion.indicadorKpi, dest=session['lang']).text
        except:
            pass
        axis.set_xlabel(string_fecha)
        axis.set_ylabel(accion.indicadorKpi)
        results = data.get("results")[::-1]
        xs = [x.fecha for x in results]
        ys = [y.kpi for y in results]
        axis.set_xticklabels(xs, rotation=45, fontsize=6)
        axis.plot(xs, ys)
        return fig
    except:
        return None


def add_account_to_allowlist(address):
    """Adds an account to the permissioned blockchain allowlist"""
    data = '{"jsonrpc":"2.0","method":"perm_addAccountsToAllowlist","params":[["' + address + '"]], "id":1}'
    response = requests.post(os.environ.get('BLOCKCHAIN_URL'), data=data)
    return response


@app.route('/')
def home():
    KPIporFechas.save_todays_KPI()
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
    c_reward = Accion.get_action_by_id(session['accionId'])
    kpi = request.form['kpi']
    str_recompensa = str(c_reward.recompensa).replace(",", ".")
    c_reward.recompensa = float(str_recompensa) * float(kpi) * 100    # The multiplication adjusts to the coin decimals
    reward_coins(session['email'], c_reward.recompensa, res['Hash'], urlProof)
    try:
        c_reward.nombre = translator.translate(c_reward.nombre, dest=session['lang']).text
    except:
        pass
    del session['accionId']
    return render_template("recompensa.html", name=session['name'], accion=c_reward, email=session['email'], user=user)


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
        c_reward = Accion.get_action_by_id(session['accionId'])
        try:
            c_reward.nombre = translator.translate(c_reward.nombre, dest=session['lang']).text
            c_reward.descripcion = translator.translate(c_reward.descripcion, dest=session['lang']).text
            c_reward.indicadorKpi = translator.translate(c_reward.indicadorKpi, dest=session['lang']).text
        except:
            pass
        if c_reward is not None:
            return render_template("subirimagen.html", name=session['name'], cReward=c_reward, email=session['email'],
                                   session=session, user=user, accionId=c_reward)
        else:
            return redirect('/wallet')
    if 'offerId' in session and user is not None:
        offer = Oferta.get_offer_by_id(session['offerId'])
        if offer is not None:
            dest = User.get_company_block_addr(offer.empresa).email
            offer_transaction(session['email'], dest, offer)
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
        keys = generate_keys()
        blockchain_address = Web3.toChecksumAddress(keys['address'])
        session['blockchainAddr'] = blockchain_address
        pk = keys['key']
        rol = request.form['rol']
        org = request.form['organizacion']

        s = Session()
        u = User(nombre, email, blockchain_address, pk, picture, rol, org)
        s.add(u)
        s.commit()
        add_account_to_allowlist(blockchain_address)   # Permite al usuario usar la blockchain permisionada
        if rol == 'Colaborador':    
            # No es necesario asignar el rol en el smart contract, ya que por defecto se asigna a colaborador
            return redirect('/wallet')
        if rol == 'Promotor':
            blockchain_manager.assign_role(caller=admin_address, callerKey=private_key, account=blockchain_address, roleID=0)
            return redirect('/accion')
    else:
        return render_template("register.html", email=email, nombre=name)


@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    form = SendUDCForm()
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    salary = get_balance(user.blockHash)
    if form.validate_on_submit():
        transfer_coins(rem=user, dest=User.get_by_email(request.form['destiny']), amount=request.form['quantity'], email=email, dest_email=request.form['destiny'])
    given_name = dict(session).get('given_name', None)
    try:
        del session['accionId']
        del session['offerId']
    except:
        pass
    return render_template('tab1cartera.html', title='Cartera', wallet=salary, email=email, name=given_name, w3=blockchain_manager.w3,
                           form=form, user=user)


@app.route('/redeemOffer/<int:offer_id>')
def redeem_offer(offer_id):
    offer = Oferta.get_offer_by_id(offer_id)
    user = User.get_by_email(session['email'])
    dest = User.get_company_block_addr(offer.empresa).email
    offer_transaction(session['email'], dest, offer)
    try:
        offer.nombre = translator.translate(offer.nombre, dest=session['lang']).text
    except:
        pass
    return render_template("pago.html", name=session['name'], offer=offer, email=session['email'],
                           session=session, user=user)


@app.route('/accion', methods=['GET', 'POST'])
def action():
    form_1 = CreateCampaignForm()    # TODO: change name of this to a better one
    form_2 = CreateOfferForm()
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)

    if user.role == "Promotor":
        campanyas = Campanya.get_campaigns(user.organizacion)
        acciones = Accion.get_actions(user.organizacion)
        ofertas = Oferta.get_offers(user.organizacion)
    elif user.role == "Administrador":
        campanyas = Campanya.get_all_campaigns()
        acciones = Accion.get_all_actions()
        ofertas = Oferta.get_all_offers()
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
    salary = get_balance(os.environ.get('ADMIN_ADDRESS'))
    if form_1.validate_on_submit() and form_1.crearCamp.data:
        s = Session()
        if user.role == "Promotor":
            c = Campanya(request.form['campaign_name'], user.organizacion, request.form['description'])
        elif user.role == "Administrador":
            c = Campanya(request.form['campaign_name'], request.form['company'], request.form['description'])
        s.add(c)
        s.commit()
    elif form_2.validate_on_submit() and form_2.crearOf.data:
        nombre = request.form['offer_name']
        s = Session()
        if user.role == "Promotor":
            o = Oferta(request.form['offer_name'], user.organizacion, request.form['description'], request.form['price'])
        elif user.role == "Administrador":
            o = Oferta(request.form['offer_name'], request.form['company'], request.form['description'], request.form['price'])
        s.add(o)
        s.commit()

    if request.method == 'POST' and 'create_action' in request.form:
        nombre = request.form['name']
        desc = request.form['description']
        recompensa = request.form['reward']
        indKpi = request.form['kpi']
        kpiObj = request.form['target']
        camp = request.form['campaign']
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
    return render_template('accion.html', title='Acción', wallet=salary, email=email, name=given_name, w3=blockchain_manager.w3,
                           form=form_1, form2=form_2, user=user, acciones=acciones, campanyas=campanyas, ofertas=ofertas)


@app.route('/accionalumnos', methods=['GET', 'POST'])
def action_students():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    salary = get_balance(user.blockHash)
    acciones = Accion.get_all_actions()
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
    return render_template('accionalumnos.html', title='Acción', wallet=salary, email=email, name=given_name, w3=blockchain_manager.w3,
                           user=user, acciones=acciones)


@app.route('/ofertas', methods=['GET', 'POST'])
def offers():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    salary = get_balance(user.blockHash)
    ofertas = Oferta.get_all_offers()
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
    return render_template('ofertas.html', title='Oferta', wallet=salary, email=email, name=given_name, w3=blockchain_manager.w3,
                           user=user, ofertas=ofertas)


@app.route('/historialtrans', methods=['GET', 'POST'])
def transaction_history():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    salary = get_balance(user.blockHash)
    name = dict(session).get('name', None)

    if user.role == "Colaborador":
        transacciones = Transaccion.get_transactions(user.email)
    elif user.role == "Promotor":
        transacciones = Transaccion.get_transactions(user.organizacion)
    else:
        transacciones = Transaccion.get_all_transactions()
    for t in transacciones:
        camp_id = t.campanya
        try:
            t.campanya = Campanya.get_campaign_by_id(camp_id).nombre
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
    return render_template('historialtrans.html', title='Acción', wallet=salary, email=email, name=name, w3=blockchain_manager.w3,
                           user=user, transacciones=transacciones)


@app.route('/editor/<int:campanya_id>', methods=['GET', 'POST'])
def editor(campanya_id):
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    acciones = Accion.get_actions_of_campaign(campanya_id)
    campanya = Campanya.get_campaign_by_id(campanya_id)
    salary = get_balance(user.blockHash)
    s = Session()
    if request.method == 'POST':
        if 'editarAcc' in request.form:
            return redirect(url_for('action_editor', accion_id=request.form['accion_id']))
        elif 'eliminarAcc' in request.form:
            query = s.query(Accion)
            pk = request.form['accion_id']
            query = query.filter(Accion.id == pk).first()
            s.delete(query)
            s.commit()
            acciones = Accion.get_actions_of_campaign(campanya_id)

    return render_template('adminacciones.html', title='Acción', wallet=salary, email=email, name=given_name, w3=blockchain_manager.w3,
                           user=user, acciones=acciones, campanya=campanya)


@app.route('/plot<int:campanya_id>.png')
def plot_png(campanya_id):
    fig = create_figure(campanya_id)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')


@app.route('/editorC', methods=['GET', 'POST'])
def campaigns_editor():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    if user.role == "Promotor":
        campanyas = Campanya.get_campaigns(user.organizacion)
    if user.role == "Administrador":
        campanyas = Campanya.get_all_campaigns()
    salary = get_balance(user.blockHash)
    s = Session()
    if request.method == 'POST':
        if 'editar' in request.form:
            return redirect(url_for('campaign_editor', campanya_id=request.form['id']))
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
                           w3=blockchain_manager.w3, user=user, campanyas=campanyas)


@app.route('/editorO', methods=['GET', 'POST'])
def offers_editor():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    if user.role == "Promotor":
        ofertas = Oferta.get_offers(user.organizacion)
    if user.role == "Administrador":
        ofertas = Oferta.get_all_offers()
    salary = get_balance(user.blockHash)
    s = Session()
    if request.method == 'POST':
        if 'editarO' in request.form:
            return redirect(url_for('offer_editor', offer_id=request.form['id']))
        elif 'eliminarO' in request.form:
            query = s.query(Oferta)
            pk = request.form['id']
            query = query.filter(Oferta.id == pk).first()
            s.delete(query)
            s.commit()
            if user.role == "Promotor":
                ofertas = Oferta.get_offers(user.organizacion)
            if user.role == "Administrador":
                ofertas = Oferta.get_all_offers()
    try:
        del session['accionId']
        del session['offerId']
    except:
        pass
    return render_template('adminofertas.html', title='Ofertas', wallet=salary, email=email, name=given_name,
                           w3=blockchain_manager.w3, user=user, ofertas=ofertas)


@app.route('/editarAcc/<int:accion_id>', methods=["GET", "POST"])
def action_editor(accion_id):
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    s = Session()
    query = s.query(Accion)
    accion = query.filter(Accion.id == accion_id).first()
    if request.method == 'POST' and 'actualizarA' in request.form:
        dictupdate = {Accion.nombre: request.form['name'], Accion.descripcion: request.form['description'],
                      Accion.recompensa: float(request.form['reward']),
                      Accion.indicadorKpi: request.form['kpi_indicator'], Accion.kpiObj: int(request.form['kpi_target'])}
        query.filter(Accion.id == accion_id).update(dictupdate, synchronize_session=False)
        s.commit()
    return render_template("editoraccion.html", accion=accion, email=email, name=given_name, user=user)


@app.route('/editorCampanyas/<int:campanya_id>', methods=["GET", "POST"])
def campaign_editor(campanya_id):
    email = dict(session).get('email', None)
    given_name = dict(session).get('given_name', None)
    user = User.get_by_email(email)

    s = Session()
    query = s.query(Campanya)
    campanya = query.filter(Campanya.id == campanya_id).first()
    if request.method == 'POST':
        dictupdate = {Campanya.nombre: request.form['name'], Campanya.descripcion: request.form['description']}
        query.filter(Campanya.id == campanya_id).update(dictupdate, synchronize_session=False)
        s.commit()
    return render_template("editorcamp.html", campanya=campanya, email=email, name=given_name,
                           user=user)


@app.route('/editorOferta/<int:offer_id>', methods=["GET", "POST"])
def offer_editor(offer_id):
    email = dict(session).get('email', None)
    given_name = dict(session).get('given_name', None)
    user = User.get_by_email(email)

    s = Session()
    query = s.query(Oferta)
    oferta = query.filter(Oferta.id == offer_id).first()
    if request.method == 'POST':
        dictupdate = {Oferta.nombre: request.form['name'], Oferta.descripcion: request.form['description'],
                      Oferta.precio: request.form['price']}
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
def qr_offers(offerId):
    img = qrcode.make(url_for('pay', offer_id=offerId, _external=True))
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
        temp_lang = session['lang']
        session.clear()
        session['lang'] = temp_lang
    except:
        pass
    return redirect('/')


@app.route('/sobre')
def about():
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
def campaigns():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    campanyas = Campanya.get_ordered_campaigns()
    empresas = Campanya.get_distinct_companies()
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
def company(emp):
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    salary = get_balance(user.blockHash)
    campanyas = Campanya.get_campaigns(emp)
    acciones = Accion.get_actions(emp)
    try:
        for c in campanyas:
            c.nombre = translator.translate(c.nombre, dest=session['lang']).text
            c.descripcion = translator.translate(c.descripcion, dest=session['lang']).text
        for a in acciones:
            a.nombre = translator.translate(a.nombre, dest=session['lang']).text
            a.descripcion = translator.translate(a.descripcion, dest=session['lang']).text
    except:
        pass
    return render_template('campanyas.html', wallet=salary, email=email, name=given_name, w3=blockchain_manager.w3,
                           user=user, campanyas=campanyas, empresa=emp, acciones=acciones)


@app.route('/registraraccion/<int:accion_id>', methods=['GET', 'POST'])
def register_action(accion_id):
    user = User.get_by_email(session['email'])
    session['accionId'] = accion_id
    c_reward = Accion.get_action_by_id(accion_id)
    try:
        c_reward.nombre = translator.translate(c_reward.nombre, dest=session['lang']).text
        c_reward.descripcion = translator.translate(c_reward.descripcion, dest=session['lang']).text
        c_reward.indicadorKpi = translator.translate(c_reward.indicadorKpi, dest=session['lang']).text
    except:
        pass
    return render_template("subirimagen.html", name=session['name'], cReward=c_reward, email=session['email'],
                           session=session, user=user, accionId=accion_id)


@app.route('/sw.js')
def sw():   # TODO: what is this?
    response = make_response(send_from_directory('static', filename='sw.js'))
    response.headers['Content-Type'] = 'application/javascript'
    return response


@app.before_request
def before_request():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)


@app.errorhandler(400)
def bad_request(e):
    return render_template("error.html", code="400", type="Bad Request"), 400


@app.errorhandler(401)
def unauthorized(e):
    return render_template("error.html", code="401", type="Unauthorized"), 401


@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code="403", type="Forbidden"), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", code="404", type="Not Found"), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template("error.html", code="500", type="Internal Server Error"), 500


if __name__ == "__main__":
    app.run()
