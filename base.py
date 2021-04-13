from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine(app.config['DATABASE_URL'])
Session = sessionmaker(bind=engine)

Base = declarative_base()
Base.metadata.create_all(engine)

def init_db():
    Base.metadata.create_all(bind=engine)
