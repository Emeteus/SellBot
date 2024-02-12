from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class RentOffer(Base):
    __tablename__ = 'rent_offers'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    price = Column(String)
    photo = Column(String)


class SaleOffer(Base):
    __tablename__ = 'sale_offers'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    price = Column(String)
    photo = Column(String)


engine = create_engine('sqlite:///offers.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
