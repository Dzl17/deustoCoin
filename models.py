from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, Boolean
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
    def get_by_email(email):
        s = Session()
        query = s.query(User)
        return query.filter(User.email==email).first()

    