from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://postgres:root@localhost:5432/deustoCoin')
Session = sessionmaker(bind=engine)

Base = declarative_base()
Base.metadata.create_all(engine)

def init_db():
    import models
    Base.metadata.create_all(bind=engine)
