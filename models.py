from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, Boolean,Float, or_
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
    def __init__(self, name, email, blockHash, picture, role):
        self.name = name
        self.email = email
        self.blockHash = blockHash
        self.picture = picture
        self.role = role

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
    transHash = Column(String(80), nullable=False)
    remitente = Column(String(50), unique=True, nullable=False)
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
    # def set_password(self, password):
    #     self.password = generate_password_hash(password)
    # def check_password(self, password):
    #     return check_password_hash(self.password, password)

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