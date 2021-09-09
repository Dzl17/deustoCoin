from sqlalchemy import Column, String, Integer, ForeignKey, Float, or_, desc
from sqlalchemy.orm import relationship, backref
from base import Base, Session
import datetime

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(256), unique=True, nullable=False)
    blockHash = Column(String(128), nullable=True)
    pk = Column(String(128), nullable=True)
    picture = Column(String(128), nullable=True)
    role = Column(String(128), nullable=False)
    organizacion = Column(String(128), nullable=False)

    def __init__(self, name, email, blockHash, pk, picture, role, organizacion):
        self.name = name
        self.email = email
        self.blockHash = blockHash
        self.pk = pk
        self.picture = picture
        self.role = role
        self.organizacion = organizacion

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
    def get_company_block_addr(compName):
        s = Session()
        query = s.query(User)
        return query.filter(User.organizacion == compName).first()

    @staticmethod
    def get_by_email(email):
        s = Session()
        query = s.query(User)
        return query.filter(User.email == email).first()

    @staticmethod
    def get_by_blockAddr(blockHash):
        s = Session()
        query = s.query(User)
        return query.filter(User.blockHash == blockHash).first()


class Transaction(Base):
    __tablename__ = 'transaccion'
    id = Column(Integer, primary_key=True)
    fecha = Column(String(80), nullable=False)
    transHash = Column(String(255), nullable=False)
    remitente = Column(String(255), nullable=False)
    destinatario = Column(String(255), nullable=False)
    campanya = Column(Integer, ForeignKey('campanya.id'),
                      nullable=True)
    cantidad = Column(Float, nullable=False)
    imgHash = Column(String(255), nullable=True)
    proof = Column(String(255), nullable=True)

    def __init__(self, fecha, transHash, remitente, destinatario, campanya, cantidad, imgHash, proof):
        self.fecha = fecha
        self.transHash = transHash
        self.remitente = remitente
        self.destinatario = destinatario
        self.campanya = campanya
        self.cantidad = cantidad
        self.imgHash = imgHash
        self.proof = proof

    def __repr__(self):
        return f'<Transaccion {self.transHash}>'

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
        return query.filter(or_(Transaction.remitente == email, Transaction.destinatario == email)).all()

    @staticmethod
    def get_all_transactions():
        s = Session()
        query = s.query(Transaction).order_by(Transaction.id)
        return query.all()


class KPIByDates(Base):
    __tablename__ = 'kpi_fechas'
    id = Column(Integer, primary_key=True)
    accion = Column(Integer, ForeignKey('accion.id', ondelete='CASCADE'))
    fecha = Column(String, nullable=False)
    kpi = Column(Integer)

    def __init__(self, fecha, accion, kpi):
        self.fecha = fecha
        self.accion = accion
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
        results = query.filter(KPIByDates.accion == id).order_by(desc(KPIByDates.id)).all()
        query2 = s.query(Action)
        name = query2.filter(Action.id == id).first().nombre
        data = {
            "name": name,
            "results": results
        }
        return data

    @staticmethod
    def save_todays_KPI():
        fechas = []
        acciones = Action.get_all_actions()
        kpis = KPIByDates.get_all_KPIs()
        if len(kpis) > 0:
            for k in kpis:
                fechas.append(k.fecha)
        dt = datetime.datetime.today()
        today = dt.strftime("%d/%m/%Y")
        if today not in fechas:
            s = Session()
            fechas.append(today)
            for a in acciones:
                kpi = KPIByDates(today, a.id, a.kpi)
                s.add(kpi)
            s.commit()
            s.close()
        else:
            pass


class Action(Base):
    __tablename__ = 'accion'
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    empresa = Column(String(255), nullable=False)
    descripcion = Column(String, unique=True, nullable=False)
    recompensa = Column(Float, nullable=False)
    indicadorKpi = Column(String, nullable=False)
    campanya_id = Column(Integer, ForeignKey('campanya.id'))
    kpi = Column(Integer, default=0)
    kpiObj = Column(Integer, default=0)
    kpis = relationship(KPIByDates, backref=backref("kpi_fechas", passive_deletes=True))

    def __init__(self, nombre, empresa, descripcion, recompensa, indicadorKpi, kpiObj, campanya_id):
        self.nombre = nombre
        self.empresa = empresa
        self.descripcion = descripcion
        self.recompensa = recompensa
        self.indicadorKpi = indicadorKpi
        self.kpiObj = kpiObj
        self.campanya_id = campanya_id

    def __repr__(self):
        return f'<Acción {self.nombre}>: {self.descripcion}'

    def save(self):
        s = Session()
        if not self.id:
            s.add(self)
        s.commit()
        s.expunge(self)
        s.close()

    @staticmethod
    def get_actions(empresa):
        s = Session()
        query = s.query(Action)
        return query.filter(Action.empresa == empresa).all()

    @staticmethod
    def get_actions_of_campaign(campanya_id):
        s = Session()
        query = s.query(Action)
        return query.filter(Action.campanya_id == campanya_id).all()

    @staticmethod
    def get_all_actions():
        s = Session()
        query = s.query(Action)
        return query.all()

    @staticmethod
    def get_id_by_name(nombre):
        s = Session()
        query = s.query(Action)
        return query.filter(Action.nombre == nombre).first().id

    @staticmethod
    def get_action_by_id(id):
        s = Session()
        query = s.query(Action)
        return query.filter(Action.id == id).first()


class Campaign(Base):
    __tablename__ = 'campanya'
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    empresa = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    acciones = relationship("Action")

    def __init__(self, nombre, empresa, descripcion):
        self.nombre = nombre
        self.empresa = empresa
        self.descripcion = descripcion

    @staticmethod
    def get_campaigns(empresa):
        s = Session()
        query = s.query(Campaign)
        return query.filter(Campaign.empresa == empresa).all()

    @staticmethod
    def get_all_campaigns():
        s = Session()
        query = s.query(Campaign)
        return query.all()

    @staticmethod
    def get_ordered_campaigns():
        s = Session()
        query = s.query(Campaign)
        query = query.order_by(Campaign.empresa).all()
        return query

    @staticmethod
    def get_distinct_companies():
        s = Session()
        query = s.query(Campaign)
        query = query.distinct(Campaign.empresa).all()
        companies = []
        for campaign in query:
            companies.append(campaign.empresa)
        return companies

    @staticmethod
    def get_id_by_name(nombre):
        s = Session()
        query = s.query(Campaign)
        return query.filter(Campaign.nombre == nombre).first()

    @staticmethod
    def get_campaign_by_id(id):
        s = Session()
        query = s.query(Campaign)
        return query.filter(Campaign.id == id).first()


class Offer(Base):
    __tablename__ = 'oferta'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(80), nullable=False)
    empresa = Column(String(80), nullable=False)
    descripcion = Column(String, nullable=True)
    precio = Column(String, nullable=False)

    def __init__(self, nombre, empresa, descripcion, precio):
        self.nombre = nombre
        self.empresa = empresa
        self.descripcion = descripcion
        self.precio = precio

    @staticmethod
    def get_offers(empresa):
        s = Session()
        query = s.query(Offer)
        return query.filter(Offer.empresa == empresa).all()

    @staticmethod
    def get_all_offers():
        s = Session()
        query = s.query(Offer)
        return query.all()

    @staticmethod
    def get_id_by_name(nombre):
        s = Session()
        query = s.query(Offer)
        return query.filter(Offer.nombre == nombre).first().id

    @staticmethod
    def get_offer_by_id(id):
        s = Session()
        query = s.query(Offer)
        return query.filter(Offer.id == id).first()
