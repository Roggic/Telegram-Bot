# coding=cp1251
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Identity, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

engine = create_engine("sqlite:///habit_stats.sqlite")


def new_session():
    engine = create_engine("sqlite:///habit_stats.sqlite")
    Session = sessionmaker(engine)
    session = Session()
    return session


Base = declarative_base()


class Users(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True)
    user_firstname = Column(String)
    user_lastname = Column(String)
    username = Column(String)

    def __init__(self, user_id, user_firstname, user_lastname, username):
        self.user_id = user_id
        self.user_firstname = user_firstname
        self.user_lastname = user_lastname
        self.username = username


class Stats(Base):
    __tablename__ = "����������"
    id = Column(Integer, Identity(start=1), primary_key=True)
    date_time = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    reason_id = Column(Integer, ForeignKey("�������.id"))
    reason = relationship("Reasons", back_populates="reason_to_stats")

    def __init__(self, date_time, user_id, reason_id):
        self.date_time = date_time
        self.user_id = user_id
        self.reason_id = reason_id


class Reasons(Base):
    __tablename__ = "�������"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    reason = Column(String, nullable=False)
    reason_to_stats = relationship("Stats", back_populates="reason")

    def __init__(self, user_id, reason):
        self.user_id = user_id
        self.reason = reason


Base.metadata.create_all(engine)


def add_data(new_data):
    """��������� ����� ������ � ���� ������. new_data ������ ���� �������� ������� (����� ������)"""
    session = new_session()
    session.add(new_data)
    session.commit()
    session.close()
