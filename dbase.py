# coding=cp1251
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Identity, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

engine = create_engine("sqlite:///habit_stats.sqlite")

Base = declarative_base()

Session = sessionmaker(engine)
session = Session()


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
    __tablename__ = "Статистика"
    id = Column(Integer, Identity(start=1), primary_key=True)
    date_time = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    reason_id = Column(Integer, ForeignKey("Причины.id"))
    reason = relationship("Reasons", back_populates="reason_to_stats")

    def __init__(self, date_time, user_id, reason_id):
        self.date_time = date_time
        self.user_id = user_id
        self.reason_id = reason_id


class Reasons(Base):
    __tablename__ = "Причины"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    reason = Column(String, nullable=False)
    reason_to_stats = relationship("Stats", back_populates="reason")

    def __init__(self, user_id, reason):
        self.user_id = user_id
        self.reason = reason


Base.metadata.create_all(engine)


def add_data(new_data):
    """Добавляет новые данные в базу данных. new_data должна быть объектом таблицы (новая строка)"""
    session.add(new_data)
    session.commit()

# Пример заполнения таблицы
# session_maker = sessionmaker(bind=engine)
# session = session_maker()
# date_time = datetime.datetime.now()
# user_id = "roggic"
# reason_id = 1
# new_row = Stats(date_time=date_time,
#                 user_id=user_id,
#                 reason_id=reason_id)
# session.add(new_row)
# session.commit()
