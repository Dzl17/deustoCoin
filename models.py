from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, Boolean,Float, or_
from sqlalchemy.orm import relationship
from base import Base, Session


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(256), unique=True, nullable=False)
    # password = db.Column(db.String(128), nullable=False)
    blockHash = Column(String(128), nullable=False)
    picture = Column(String(128), nullable=True)
    role = Column(String(128), nullable=False)
    organizacion = Column(String(128), nullable=False)

    def __init__(self, name, email, blockHash, picture, role, organizacion):
        self.name = name
        self.email = email
        self.blockHash = blockHash
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
    def get_by_email(email):
        s = Session()
        query = s.query(User)
        return query.filter(User.email==email).first()
    


class Transaccion(Base):
    __tablename__ = 'transaccion'
    id = Column(Integer, primary_key=True)
    fecha = Column(String(80), nullable=False)
    transHash = Column(String(255), nullable=False)
    remitente = Column(String(50), nullable=False)
    destinatario = Column(String(50), nullable=False)
    cantidad = Column(Float, nullable=False)

    def __init__(self, fecha, transHash, remitente, destinatario, cantidad):
        self.fecha = fecha
        self.transHash = transHash
        self.remitente = remitente
        self.destinatario = destinatario
        self.cantidad = cantidad

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
    def getTransactions(email):
        s = Session()
        query = s.query(Transaccion)
        return query.filter(or_(Transaccion.remitente==email, Transaccion.destinatario==email)).all()

class Accion(Base):
    __tablename__ = 'accion'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(80), nullable=False)
    empresa = Column(String(80), nullable=False)
    descripcion = Column(String, unique=True, nullable=False)
    recompensa = Column(Float, nullable=False)
    campanya_id = Column(Integer, ForeignKey('campanya.id'))

    def __init__(self, nombre, empresa, descripcion, recompensa):
        self.nombre = nombre
        self.empresa = empresa
        self.descripcion = descripcion
        self.recompensa = recompensa

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
    def getActions(empresa):
        s = Session()
        query = s.query(Accion)
        return query.filter(Accion.empresa==empresa).all()
    @staticmethod
    def getAllActions():
        s = Session()
        query = s.query(Accion)
        return query.all()
    @staticmethod
    def getIdByName(nombre):
        s = Session()
        query = s.query(Accion)
        return query.filter(Accion.nombre==nombre).first().id
    @staticmethod
    def getActionById(id):
        s = Session()
        query = s.query(Accion)
        return query.filter(Accion.id==id).first()

class Campanya(Base):
    __tablename__ = 'campanya'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(80), nullable=False)
    empresa = Column(String(80), nullable=False)
    descripcion = Column(String, nullable=False)
    acciones = relationship("Accion")

    def __init__(self, nombre, empresa, descripcion):
        self.nombre = nombre
        self.empresa = empresa
        self.descripcion = descripcion

    @staticmethod
    def getCampaigns(empresa):
        s = Session()
        query = s.query(Campanya)
        return query.filter(Campanya.empresa==empresa).all()
    @staticmethod
    def getCampaignNames(empresa):
        s = Session()
        query = s.query(Campanya)
        arrayCamps = query.filter(Campanya.empresa==empresa).all()
        arrayNames = []
        for i in arrayCamps:
            arrayNames.append(i.nombre)
        return arrayNames
    @staticmethod
    def getAllCampaigns():
        s = Session()
        query = s.query(Campanya)
        return query.all()
    @staticmethod
    def getIdByName(nombre):
        s = Session()
        query = s.query(Campanya)
        return query.filter(Campanya.nombre==nombre).first().id
    @staticmethod
    def getCampaignById(id):
        s = Session()
        query = s.query(Campanya)
        return query.filter(Campanya.id==id).first()