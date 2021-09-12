from sqlalchemy import Column, String, Integer, ForeignKey, Float, or_, desc
from sqlalchemy.orm import relationship, backref
from base import Base, Session
import datetime

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(256), unique=True, nullable=False)
    block_addr = Column('blockHash', String(128), nullable=True)
    pk = Column(String(128), nullable=True)
    picture = Column(String(128), nullable=True)
    role = Column(String(128), nullable=False)
    organization = Column('organizacion', String(128), nullable=False)

    def __init__(self, name, email, block_addr, pk, picture, role, organization):
        self.name = name
        self.email = email
        self.block_addr = block_addr
        self.pk = pk
        self.picture = picture
        self.role = role
        self.organization = organization

    def __repr__(self):
        return f'<User {self.email}>'

    def save(self):
        s = Session()
        if not self.id:
            s.add(self)
        s.commit()
        s.expunge(self)
        s.close()

    @staticmethod
    def get_company_block_addr(comp_name):
        s = Session()
        query = s.query(User)
        return query.filter(User.organization == comp_name).first()

    @staticmethod
    def get_by_email(email):
        s = Session()
        query = s.query(User)
        return query.filter(User.email == email).first()

    @staticmethod
    def get_by_blockAddr(block_addr):
        s = Session()
        query = s.query(User)
        return query.filter(User.block_addr == block_addr).first()


class Transaction(Base):
    __tablename__ = 'transaccion'
    id = Column(Integer, primary_key=True)
    date = Column('fecha', String(80), nullable=False)
    transaction_hash = Column('transHash', String(255), nullable=False)
    sender = Column('remitente', String(255), nullable=False)
    receiver = Column('destinatario', String(255), nullable=False)
    campaign = Column('campanya', Integer, ForeignKey('campanya.id'), nullable=True)
    quantity = Column('cantidad', Float, nullable=False)
    img_hash = Column('imgHash', String(255), nullable=True)
    proof = Column(String(255), nullable=True)

    def __init__(self, date, transaction_hash, sender, receiver, campaign, quantity, img_hash, proof):
        self.date = date
        self.transaction_hash = transaction_hash
        self.sender = sender
        self.receiver = receiver
        self.campaign = campaign
        self.quantity = quantity
        self.img_hash = img_hash
        self.proof = proof

    def __repr__(self):
        return f'<Transaction {self.transaction_hash}>'

    def save(self):
        s = Session()
        if not self.id:
            s.add(self)
        s.commit()
        s.expunge(self)
        s.close()

    @staticmethod
    def get_transactions(email):
        s = Session()
        query = s.query(Transaction).order_by(Transaction.id)
        return query.filter(or_(Transaction.sender == email, Transaction.receiver == email)).all()

    @staticmethod
    def get_all_transactions():
        s = Session()
        query = s.query(Transaction).order_by(Transaction.id)
        return query.all()


class KPIByDates(Base):
    __tablename__ = 'kpi_fechas'
    id = Column(Integer, primary_key=True)
    action = Column('accion', Integer, ForeignKey('accion.id', ondelete='CASCADE'))
    date = Column('fecha', String, nullable=False)
    kpi = Column(Integer)

    def __init__(self, date, action, kpi):
        self.action = action
        self.date = date
        self.kpi = kpi

    @staticmethod
    def get_all_KPIs():
        s = Session()
        query = s.query(KPIByDates)
        return query.all()

    @staticmethod
    def get_graph_data(id):
        s = Session()
        query = s.query(KPIByDates)
        results = query.filter(KPIByDates.action == id).order_by(desc(KPIByDates.id)).all()
        query2 = s.query(Action)
        name = query2.filter(Action.id == id).first().name
        data = {
            "name": name,
            "results": results
        }
        return data

    @staticmethod
    def save_todays_KPI():
        dates = []
        actions = Action.get_all_actions()
        kpis = KPIByDates.get_all_KPIs()
        if len(kpis) > 0:
            for k in kpis:
                dates.append(k.date)
        dt = datetime.datetime.today()
        today = dt.strftime("%d/%m/%Y")
        if today not in dates:
            s = Session()
            dates.append(today)
            for a in actions:
                kpi = KPIByDates(today, a.id, a.kpi)
                s.add(kpi)
            s.commit()
            s.close()
        else:
            pass


class Action(Base):
    __tablename__ = 'accion'
    id = Column(Integer, primary_key=True)
    name = Column('nombre', String, nullable=False)
    company = Column('empresa', String(255), nullable=False)
    description = Column('descripcion', String, unique=True, nullable=False)
    reward = Column('recompensa', Float, nullable=False)
    kpi_indicator = Column('indicadorKpi', String, nullable=False)
    campaign_id = Column('campanya_id', Integer, ForeignKey('campanya.id'))
    kpi = Column(Integer, default=0)
    kpi_target = Column('kpiObj', Integer, default=0)
    kpis = relationship(KPIByDates, backref=backref("kpi_fechas", passive_deletes=True))

    def __init__(self, name, company, description, reward, kpi_indicator, kpi_target, campaign_id):
        self.name = name
        self.company = company
        self.description = description
        self.reward = reward
        self.kpi_indicator = kpi_indicator
        self.kpi_target = kpi_target
        self.campaign_id = campaign_id

    def __repr__(self):
        return f'<Action {self.name}>: {self.description}'

    def save(self):
        s = Session()
        if not self.id:
            s.add(self)
        s.commit()
        s.expunge(self)
        s.close()

    @staticmethod
    def get_actions(company):
        s = Session()
        query = s.query(Action)
        return query.filter(Action.company == company).all()

    @staticmethod
    def get_actions_of_campaign(campaign_id):
        s = Session()
        query = s.query(Action)
        return query.filter(Action.campaign_id == campaign_id).all()

    @staticmethod
    def get_all_actions():
        s = Session()
        query = s.query(Action)
        return query.all()

    @staticmethod
    def get_id_by_name(name):
        s = Session()
        query = s.query(Action)
        return query.filter(Action.name == name).first().id

    @staticmethod
    def get_action_by_id(id):
        s = Session()
        query = s.query(Action)
        return query.filter(Action.id == id).first()


class Campaign(Base):
    __tablename__ = 'campanya'
    id = Column(Integer, primary_key=True)
    name = Column('nombre', String, nullable=False)
    company = Column('empresa', String, nullable=False)
    description = Column('descripcion', String, nullable=False)
    actions = relationship("Action")

    def __init__(self, name, company, description):
        self.name = name
        self.company = company
        self.description = description

    @staticmethod
    def get_campaigns(company):
        s = Session()
        query = s.query(Campaign)
        return query.filter(Campaign.company == company).all()

    @staticmethod
    def get_all_campaigns():
        s = Session()
        query = s.query(Campaign)
        return query.all()

    @staticmethod
    def get_ordered_campaigns():
        s = Session()
        query = s.query(Campaign)
        query = query.order_by(Campaign.company).all()
        return query

    @staticmethod
    def get_distinct_companies():
        s = Session()
        query = s.query(Campaign)
        query = query.distinct(Campaign.company).all()
        companies = []
        for campaign in query:
            companies.append(campaign.company)
        return companies

    @staticmethod
    def get_id_by_name(name):
        s = Session()
        query = s.query(Campaign)
        return query.filter(Campaign.name == name).first()

    @staticmethod
    def get_campaign_by_id(id):
        s = Session()
        query = s.query(Campaign)
        return query.filter(Campaign.id == id).first()


class Offer(Base):
    __tablename__ = 'oferta'
    id = Column(Integer, primary_key=True)
    name = Column('nombre', String(80), nullable=False)
    company = Column('empresa', String(80), nullable=False)
    description = Column('descripcion', String, nullable=True)
    price = Column('precio', String, nullable=False)

    def __init__(self, name, company, description, price):
        self.name = name
        self.company = company
        self.description = description
        self.price = price

    @staticmethod
    def get_offers(company):
        s = Session()
        query = s.query(Offer)
        return query.filter(Offer.company == company).all()

    @staticmethod
    def get_all_offers():
        s = Session()
        query = s.query(Offer)
        return query.all()

    @staticmethod
    def get_id_by_name(name):
        s = Session()
        query = s.query(Offer)
        return query.filter(Offer.name == name).first().id

    @staticmethod
    def get_offer_by_id(id):
        s = Session()
        query = s.query(Offer)
        return query.filter(Offer.id == id).first()
