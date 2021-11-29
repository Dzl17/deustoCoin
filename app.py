from functools import reduce
from flask import Flask, url_for, render_template, request, redirect, Response, session, \
    send_from_directory, make_response, abort
from flask_babel import Babel, gettext
from authlib.integrations.flask_client import OAuth
from base import Session, init_db
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from models import User, Transaction, Action, Campaign, KPIByDates, Offer
from datetime import datetime, time
from forms import SendUDCForm, CreateCampaignForm, CreateOfferForm
from googletrans import Translator
from flask.cli import with_appcontext
from contracts import *
import base58
import io
import qrcode
import os
import requests
import time

admin_address = os.environ.get('ADMIN_ADDRESS')
admin_key = os.environ.get('PRIVATE_KEY')
blockchain_manager = BlockchainManager()

app = Flask(__name__)
app.secret_key = admin_key
app.config['PRIVATE_KEY'] = admin_key
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
    return blockchain_manager.balance_of(address)/100    # Divide to create equivalence to the Euro, as a single UDC is equivalent to a cent


def decode_hash(hash):
    """Turns an IPFS hash into a value that can be stored in the Smart Contract.\n
    The hash is returned in a base58 multihash, from which the first two bytes are removed, as they represent the hash function and the length in bytes, which we don't need."""
    decoded_hash = base58.b58decode(hash)
    reduced_hash = decoded_hash.hex()[4:]
    return reduced_hash


def reward_coins(dest, promoter, action_id, amount, img_hash, url_proof):
    """Reward the input amount of coins to the user that completes a good deed."""
    dest_user = User.get_by_email(dest)
    dest_address = dest_user.block_addr
    promoter_address = promoter.block_addr
    promoter_balance = get_balance(promoter_address)
    # Avoid trying to reward more than the promoter's balance; this is already enforced on the 
    # smart contract, but here the rest of the balance is sent if there's not enough for the whole reward
    reward = int(float(amount)*100) if promoter_balance > int(float(amount)*100) else promoter_balance
    action = Action.get_action_by_id(session['action_id'])

    tx_hash = blockchain_manager.processAction(caller=admin_address, caller_key=admin_key, promoter=promoter_address, 
        to=dest_address, action_id=action_id, reward=int(reward), time=int(time.time()), ipfs_hash=img_hash)

    s = Session()
    datetime_obj = datetime.now()
    timestamp_str = datetime_obj.strftime("%d-%m-%Y (%H:%M:%S.%f)")
    t = Transaction(timestamp_str, tx_hash, action.company, dest, action.campaign_id, amount, img_hash, url_proof)
    s.add(t)
    s.commit()
    query = s.query(Action)
    kpi = int(float(request.form['kpi']))
    dictupdate = {Action.kpi: Action.kpi + kpi}
    query.filter(Action.id == action.id).update(dictupdate, synchronize_session=False)
    s.commit()
    s.close()


def offer_transaction(sender, dest, offer):
    """Pay to a company in exchange for an offer."""
    dest_user = User.get_by_email(dest)
    dest_address = dest_user.block_addr
    sender_user = User.get_by_email(sender)
    sender_address = sender_user.block_addr
    sender_key = sender_user.pk
    value = int(float(offer.price)*100)

    tx_hash = blockchain_manager.burn(caller=admin_address, caller_key=admin_key, from_acc=sender_address, value=value)

    s = Session()
    datetime_obj = datetime.now()
    timestamp_str = datetime_obj.strftime("%d-%m-%Y (%H:%M:%S.%f)")
    t = Transaction(timestamp_str, tx_hash, sender, dest_user.organization, None, offer.price, "", "")
    s.add(t)
    s.commit()
    s.close()


def transfer_coins(sender, dest, amount, email, dest_email):
    """Transfer coins to another user."""
    owner_address = sender.block_addr
    dest_address = dest.block_addr
    value=int(float(amount)*100)

    tx_hash = blockchain_manager.transfer(caller=owner_address, caller_key=sender.pk, to=dest_address, value=value)

    s = Session()
    datetime_obj = datetime.now()
    timestamp_str = datetime_obj.strftime("%d-%b-%Y (%H:%M:%S.%f)")
    t = Transaction(timestamp_str, tx_hash, email, dest_email, None, amount, "", "")
    s.add(t)
    s.commit()


def create_figure(id):
    """Generates a Matplotlib visualization of a given action."""
    try:
        fig = Figure()
        axis = fig.add_subplot(1, 1, 1)
        action = Action.get_action_by_id(id)
        data = KPIByDates.get_graph_data(id)
        title = data.get("name")
        axis.set_title(title + " - " + action.kpi_indicator)
        axis.set_ylim(0, action.kpi_target)
        date_string = "Fecha"
        try:
            date_string = translator.translate(date_string, dest=session['lang']).text
            action.kpi_indicator = translator.translate(action.kpi_indicator, dest=session['lang']).text
        except:
            pass
        axis.set_xlabel(date_string)
        axis.set_ylabel(action.kpi_indicator)
        results = data.get("results")[::-1]
        xs = [x.date for x in results]
        ys = [y.kpi for y in results]
        axis.set_xticklabels(xs, rotation=45, fontsize=6)
        axis.plot(xs, ys)
        return fig
    except:
        return None


def add_account_to_allowlist(address):
    """Adds an account to the permissioned blockchain allowlist."""
    data = '{"jsonrpc":"2.0","method":"perm_addAccountsToAllowlist","params":[["' + address + '"]], "id":1}'
    response = requests.post(os.environ.get('BLOCKCHAIN_URL'), data=data)
    return response


def ipfs_add_file(file):
    """Uploads a file to IPFS."""
    files = {
        'image': (file.filename, file.read(), 'rb'),
    }
    params = (
        ('hash', 'sha2-256'),
    )
    response = requests.post(os.environ.get('IPFS_URL'), files=files, params=params)
    print(response)
    return response


@app.route('/')
def home():
    KPIByDates.save_todays_KPI()
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
    user = User.get_by_email(session['email'])
    try:
        url_proof = request.form['proof']
    except:
        url_proof = ""
    file = request.files['filename']
    res = ipfs_add_file(file)
    c_reward = Action.get_action_by_id(session['action_id'])
    kpi = request.form['kpi']
    str_reward = str(c_reward.reward).replace(",", ".")
    c_reward.reward = float(str_reward) * float(kpi) * 100    # The multiplication adjusts to the coin decimals
    company = User.get_company_block_addr(c_reward.company)

    decoded_hash = '0x' + decode_hash(res.json()['Hash'])
    # Important: the 'img_hash' parameter must be a valid bytes32 hash (e.g. '0x64EC88CA00B268E5BA1A35678A1B5316D212F4F366B2477232534A8AECA37F3C')
    reward_coins(dest=session['email'], promoter=company, action_id=session['action_id'], amount=c_reward.reward, img_hash=decoded_hash, url_proof=url_proof)
    try:
        c_reward.name = translator.translate(c_reward.name, dest=session['lang']).text
    except:
        pass
    del session['action_id']
    return render_template("recompensa.html", name=session['name'], action=c_reward, email=session['email'], user=user)


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

    if 'action_id' in session and user is not None:
        c_reward = Action.get_action_by_id(session['action_id'])
        try:
            c_reward.name = translator.translate(c_reward.name, dest=session['lang']).text
            c_reward.description = translator.translate(c_reward.description, dest=session['lang']).text
            c_reward.kpi_indicator = translator.translate(c_reward.kpi_indicator, dest=session['lang']).text
        except:
            pass
        if c_reward is not None:
            return render_template("subirimagen.html", name=session['name'], c_reward=c_reward, email=session['email'],
                                   session=session, user=user, action_id=c_reward)
        else:
            return redirect('/wallet')
    if 'offer_id' in session and user is not None:
        offer = Offer.get_offer_by_id(session['offer_id'])
        if offer is not None:
            dest = User.get_company_block_addr(offer.company).email
            offer_transaction(session['email'], dest, offer)
            try:
                offer.name = translator.translate(offer.name, dest=session['lang']).text
            except:
                pass
            return render_template("pago.html", name=session['name'], offer=offer, email=session['email'],
                                   session=session, user=user)
        else:
            return redirect('/wallet')
    else:
        if user is not None:
            if user.role == 'Collaborator':
                return redirect('/wallet')
            else:
                return redirect('/dashboard')

        else:
            return redirect('/register')


@app.route('/register', methods=['GET', 'POST'])
def register():
    email = dict(session).get('email', None)
    name = dict(session).get('name', None)
    picture = dict(session).get('picture', None)
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        keys = generate_keys()
        blockchain_address = Web3.toChecksumAddress(keys['address'])
        session['blockchain_address'] = blockchain_address
        pk = keys['key']
        role = request.form['role']
        org = request.form['organization']

        s = Session()
        u = User(name, email, blockchain_address, pk, picture, role, org)
        s.add(u)
        s.commit()
        add_account_to_allowlist(blockchain_address)   # Allows the new registered user to use the permissioned blockchain
        if role == 'Collaborator':
            return redirect('/wallet')
        if role == 'Promoter':
            return redirect('/dashboard')
    else:
        return render_template("register.html", email=email, name=name)


@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    form = SendUDCForm()
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    salary = get_balance(user.block_addr)
    if form.validate_on_submit():
        destination = User.get_by_email(request.form['destiny'])
        if destination != None:
            transfer_coins(sender=user, dest=destination, amount=request.form['quantity'], 
                email=email, dest_email=request.form['destiny'])
        else:
            given_name = dict(session).get('given_name', None)
            try:
                del session['action_id']
                del session['offer_id']
            except:
                pass
            return render_template('tab1cartera.html', title='Cartera', wallet=salary, email=email, name=given_name, 
                w3=blockchain_manager.w3, form=form, user=user, nouser=1)
    given_name = dict(session).get('given_name', None)
    try:
        del session['action_id']
        del session['offer_id']
    except:
        pass
    return render_template('tab1cartera.html', title='Cartera', wallet=salary, email=email, name=given_name, w3=blockchain_manager.w3,
                           form=form, user=user, nouser=0)


@app.route('/redeem-offer/<int:offer_id>')
def redeem_offer(offer_id):
    offer = Offer.get_offer_by_id(offer_id)
    user = User.get_by_email(session['email'])
    dest = User.get_company_block_addr(offer.company).email
    offer_transaction(session['email'], dest, offer)
    try:
        offer.name = translator.translate(offer.name, dest=session['lang']).text
    except:
        pass
    return render_template("pago.html", name=session['name'], offer=offer, email=session['email'],
                           session=session, user=user)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    campaign_form = CreateCampaignForm()
    offer_form = CreateOfferForm()
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)

    if campaign_form.validate_on_submit() and 'create_campaign' in request.form:
        s = Session()
        if user.role == 'Promoter':
            c = Campaign(request.form['campaign_name'], user.organization, request.form['description'])
        elif user.role == 'Administrator':
            c = Campaign(request.form['campaign_name'], request.form['company'], request.form['description'])
        s.add(c)
        s.commit()
        return redirect(url_for('dashboard'))
    elif offer_form.validate_on_submit() and 'create_offer' in request.form:
        s = Session()
        if user.role == 'Promoter':
            o = Offer(request.form['offer_name'], user.organization, request.form['description'], request.form['price'])
        elif user.role == 'Administrator':
            o = Offer(request.form['offer_name'], request.form['company'], request.form['description'], request.form['price'])
        s.add(o)
        s.commit()
        return redirect(url_for('dashboard'))
    if request.method == 'POST' and 'create_action' in request.form:
        offer_name = request.form['name']
        desc = request.form['description']
        reward = request.form['reward']
        kpi_indicator = request.form['kpi']
        kpi_target = request.form['target']
        campaign = request.form['campaign']

        company_address = User.get_by_email(session['email']).block_addr
        action_value = int(float(reward) * float(kpi_target) * 100)

        tx_hash = blockchain_manager.mint(caller=admin_address, caller_key=admin_key, to=company_address, value=action_value)

        s = Session()
        a = Action(offer_name, user.organization, desc, reward, kpi_indicator, kpi_target, campaign)
        s.add(a)
        s.commit()
        return redirect(url_for('dashboard'))
    if user.role == 'Promoter':
        campaigns = Campaign.get_campaigns(user.organization)
        actions = Action.get_actions(user.organization)
        offers = Offer.get_offers(user.organization)
    elif user.role == 'Administrator':
        campaigns = Campaign.get_all_campaigns()
        actions = Action.get_all_actions()
        offers = Offer.get_all_offers()
    else:
        return redirect('/login')
    try:
        for c in campaigns:
            c.name = translator.translate(c.name, dest=session['lang']).text
            c.description = translator.translate(c.description, dest=session['lang']).text
        for a in actions:
            a.name = translator.translate(a.name, dest=session['lang']).text
            a.description = translator.translate(a.description, dest=session['lang']).text
            a.kpi_indicator = translator.translate(a.kpi_indicator, dest=session['lang']).text
        for o in offers:
            o.name = translator.translate(o.name, dest=session['lang']).text
            o.description = translator.translate(o.description, dest=session['lang']).text
    except:
        pass

    try:
        del session['action_id']
        del session['offer_id']
    except:
        pass
    # Delete keys to avoid cookie conflicts
    return render_template('accion.html', title='Acción', email=email, name=given_name, w3=blockchain_manager.w3,
                           form=campaign_form, form2=offer_form, user=user, actions=actions, campaigns=campaigns, offers=offers)


@app.route('/campaigns')
def campaigns():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    campaigns = Campaign.get_ordered_campaigns()
    companies = Campaign.get_distinct_companies()
    try:
        for c in campaigns:
            c.name = translator.translate(c.name, dest=session['lang']).text
            c.description = translator.translate(c.description, dest=session['lang']).text
    except:
        pass
    try:
        del session['action_id']
        del session['offer_id']
    except:
        pass
    return render_template('empresas.html', email=email, name=given_name, user=user, campaigns=campaigns, companies=companies)


@app.route('/campaigns/<company>', methods=['GET', 'POST'])
def company(company):
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    salary = get_balance(user.block_addr)
    campaigns = Campaign.get_campaigns(company)
    actions = Action.get_actions(company)
    try:
        for c in campaigns:
            c.name = translator.translate(c.name, dest=session['lang']).text
            c.description = translator.translate(c.description, dest=session['lang']).text
        for a in actions:
            a.name = translator.translate(a.name, dest=session['lang']).text
            a.description = translator.translate(a.description, dest=session['lang']).text
    except:
        pass
    return render_template('campanyas.html', wallet=salary, email=email, name=given_name, w3=blockchain_manager.w3,
                           user=user, campaigns=campaigns, company=company, actions=actions)


@app.route('/actions', methods=['GET', 'POST'])
def actions():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    salary = get_balance(user.block_addr)
    actions = Action.get_all_actions()
    try:
        for a in actions:
            a.name = translator.translate(a.name, dest=session['lang']).text
            a.description = translator.translate(a.description, dest=session['lang']).text
    except:
        pass
    try:
        del session['action_id']
        del session['offer_id']
    except:
        pass
    return render_template('accionalumnos.html', title='Acción', wallet=salary, email=email, name=given_name, w3=blockchain_manager.w3,
                           user=user, actions=actions)


@app.route('/register-action/<int:action_id>', methods=['GET', 'POST'])
def register_action(action_id):
    user = User.get_by_email(session['email'])
    session['action_id'] = action_id
    c_reward = Action.get_action_by_id(action_id)
    try:
        c_reward.name = translator.translate(c_reward.name, dest=session['lang']).text
        c_reward.description = translator.translate(c_reward.description, dest=session['lang']).text
        c_reward.kpi_indicator = translator.translate(c_reward.kpi_indicator, dest=session['lang']).text
    except:
        pass
    return render_template("subirimagen.html", name=session['name'], c_reward=c_reward, email=session['email'],
                           session=session, user=user, action_id=action_id)


@app.route('/offers', methods=['GET', 'POST'])
def offers():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    salary = get_balance(user.block_addr)
    offers = Offer.get_all_offers()
    try:
        for o in offers:
            o.name = translator.translate(o.name, dest=session['lang']).text
            o.description = translator.translate(o.description, dest=session['lang']).text
    except:
        pass
    try:
        del session['action_id']
        del session['offer_id']
    except:
        pass
    return render_template('ofertas.html', title='Oferta', wallet=salary, email=email, name=given_name, w3=blockchain_manager.w3,
                           user=user, offers=offers)


@app.route('/campaign-editor', methods=['GET', 'POST'])
def campaigns_admin():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    if user.role == 'Promoter':
        campaigns = Campaign.get_campaigns(user.organization)
    if user.role == 'Administrator':
        campaigns = Campaign.get_all_campaigns()
    salary = get_balance(user.block_addr)
    s = Session()
    if request.method == 'POST':
        if 'edit_campaign' in request.form:
            return redirect(url_for('campaign_editor', campaign_id=request.form['id']))
        elif 'delete_campaign' in request.form:
            query = s.query(Campaign)
            pk = request.form['id']
            query = query.filter(Campaign.id == pk).first()
            s.delete(query)
            s.commit()
            if user.role == 'Promoter':
                campaigns = Campaign.get_campaigns(user.organization)
            if user.role == 'Administrator':
                campaigns = Campaign.get_all_campaigns()
        elif 'view_actions' in request.form:
            return redirect(url_for('dashboard', campaign_id=request.form['id']))
    try:
        del session['action_id']
        del session['offer_id']
    except:
        pass
    return render_template('admincampanyas.html', title='Campañas', wallet=salary, email=email, name=given_name,
                           w3=blockchain_manager.w3, user=user, campaigns=campaigns)


@app.route('/campaign-editor/<int:campaign_id>', methods=["GET", "POST"])
def campaign_editor(campaign_id):
    email = dict(session).get('email', None)
    given_name = dict(session).get('given_name', None)
    user = User.get_by_email(email)

    s = Session()
    query = s.query(Campaign)
    campaign = query.filter(Campaign.id == campaign_id).first()
    if (campaign == None):
        abort(404)
    if request.method == 'POST':
        dictupdate = {Campaign.name: request.form['name'], Campaign.description: request.form['description']}
        query.filter(Campaign.id == campaign_id).update(dictupdate, synchronize_session=False)
        s.commit()
        return redirect('/campaign-editor')
    return render_template("editorcamp.html", campaign=campaign, email=email, name=given_name, user=user)


@app.route('/action-editor/<int:campaign_id>', methods=['GET', 'POST'])
def actions_admin(campaign_id):
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    actions = Action.get_actions_of_campaign(campaign_id)
    campaign = Campaign.get_campaign_by_id(campaign_id)
    salary = get_balance(user.block_addr)
    s = Session()
    if request.method == 'POST':
        if 'edit_action' in request.form:
            return redirect(url_for('action_editor', action_id=request.form['action_id']))
        elif 'delete_action' in request.form:
            query = s.query(Action)
            pk = request.form['action_id']
            query = query.filter(Action.id == pk).first()
            s.delete(query)
            s.commit()
            actions = Action.get_actions_of_campaign(campaign_id)

    return render_template('adminacciones.html', title='Acción', wallet=salary, email=email, name=given_name, w3=blockchain_manager.w3,
                           user=user, actions=actions, campaign=campaign)


@app.route('/action-editor/<int:action_id>', methods=["GET", "POST"])
def action_editor(action_id):
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    s = Session()
    query = s.query(Action)
    action = query.filter(Action.id == action_id).first()
    if (action == None):
        abort(404)
    if request.method == 'POST' and 'update_action' in request.form:
        dictupdate = {Action.name: request.form['name'], Action.description: request.form['description'],
                      Action.reward: float(request.form['reward']),
                      Action.kpi_indicator: request.form['kpi_indicator'], Action.kpi_target: int(request.form['kpi_target'])}
        query.filter(Action.id == action_id).update(dictupdate, synchronize_session=False)
        s.commit()
        return redirect(url_for('dashboard', campaign_id=action.campaign_id))
    return render_template("editoraccion.html", action=action, email=email, name=given_name, user=user)


@app.route('/offer-editor', methods=['GET', 'POST'])
def offers_admin():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    if user.role == 'Promoter':
        offers = Offer.get_offers(user.organization)
    if user.role == 'Administrator':
        offers = Offer.get_all_offers()
    salary = get_balance(user.block_addr)
    s = Session()
    if request.method == 'POST':
        if 'edit_offer' in request.form:
            return redirect(url_for('offer_editor', offer_id=request.form['id']))
        elif 'delete_offer' in request.form:
            query = s.query(Offer)
            pk = request.form['id']
            query = query.filter(Offer.id == pk).first()
            s.delete(query)
            s.commit()
            if user.role == 'Promoter':
                offers = Offer.get_offers(user.organization)
            if user.role == 'Administrator':
                offers = Offer.get_all_offers()
    try:
        del session['action_id']
        del session['offer_id']
    except:
        pass
    return render_template('adminofertas.html', title='Ofertas', wallet=salary, email=email, name=given_name,
                           w3=blockchain_manager.w3, user=user, offers=offers)


@app.route('/offer-editor/<int:offer_id>', methods=["GET", "POST"])
def offer_editor(offer_id):
    email = dict(session).get('email', None)
    given_name = dict(session).get('given_name', None)
    user = User.get_by_email(email)

    s = Session()
    query = s.query(Offer)
    offer = query.filter(Offer.id == offer_id).first()
    if (offer == None):
        abort(404)
    if request.method == 'POST':
        dictupdate = {Offer.name: request.form['name'], Offer.description: request.form['description'],
                      Offer.price: request.form['price']}
        query.filter(Offer.id == offer_id).update(dictupdate, synchronize_session=False)
        s.commit()
        return redirect('/offer-editor')
    return render_template("editoroferta.html", offer=offer, email=email, name=given_name, user=user)


@app.route('/plot<int:campaign_id>.png')
def plot_png(campaign_id):
    fig = create_figure(campaign_id)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')


@app.route('/qr/<int:action_id>')
def qr(action_id):
    img = qrcode.make(url_for('redeem', action_id=action_id, _external=True))
    with io.BytesIO() as output:
        img.save(output, format="PNG")
        contents = output.getvalue()
    return Response(contents, mimetype='image/png')


@app.route('/qr-offers/<int:offer_id>')
def qr_offers(offer_id):
    img = qrcode.make(url_for('pay', offer_id=offer_id, _external=True))
    with io.BytesIO() as output:
        img.save(output, format="PNG")
        contents = output.getvalue()
    return Response(contents, mimetype='image/png')


@app.route('/redeem/<int:action_id>', methods=["GET", "POST"])
def redeem(action_id):
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    session['action_id'] = action_id
    return google.authorize_redirect(redirect_uri)


@app.route('/pay/<int:offer_id>', methods=["GET", "POST"])
def pay(offer_id):
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    session['offer_id'] = offer_id
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


@app.route('/about')
def about():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    given_name = dict(session).get('given_name', None)
    try:
        del session['action_id']
        del session['offer_id']
    except:
        pass
    return render_template('sobre.html', email=email, name=given_name, user=user)


@app.route('/transaction-history', methods=['GET', 'POST'])
def transaction_history():
    email = dict(session).get('email', None)
    user = User.get_by_email(email)
    salary = get_balance(user.block_addr)
    name = dict(session).get('name', None)

    if user.role == 'Collaborator':
        transactions = Transaction.get_transactions(user.email)
    elif user.role == 'Promoter':
        transactions = Transaction.get_transactions(user.organization)
    else:
        transactions = Transaction.get_all_transactions()

    all_campaigns = Campaign.get_all_campaigns()
    for t in transactions:
        camp_id = t.campaign
        for c in all_campaigns:
            if c.id == camp_id:
                t.campaign = c.name
                try:
                    t.campaign = translator.translate(t.campaign, dest=session['lang']).text
                except:
                    pass
                break

    try:
        del session['action_id']
        del session['offer_id']
    except:
        pass
    return render_template('historialtrans.html', title='Acción', wallet=salary, email=email, name=name, w3=blockchain_manager.w3,
                           user=user, transactions=transactions)


@app.route('/sw.js')
def sw():
    """Service worker."""
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
