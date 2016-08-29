from .test_base import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Time
from sqlalchemy.orm import relationship


class Account(Base):
    __tablename__ = 'accounts'
    id          = Column(Integer, primary_key=True)
    name        = Column(String(50), unique=True)
    owner       = Column(String(50), unique=True)

class Company(Base):
    __tablename__ = 'companies'
    id          = Column(Integer, primary_key=True)
    name        = Column(String(50), unique=True)
    employees   = relationship('Employee')

class Employee(Base):
    __tablename__ = 'employees'
    id          = Column(Integer, primary_key=True)
    name        = Column(String(50), unique=True)
    joined      = Column(DateTime())
    left        = Column(DateTime(), nullable=True)
    company_id  = Column(Integer, ForeignKey('companies.id'), nullable=True)
    company     = relationship('Company', back_populates='employees')
    pay_rate    = Column(Numeric(scale=4), nullable=True)
    start_time  = Column(Time, nullable=True)
    lunch_start = Column(Time, nullable=True)
    end_time    = Column(Time, nullable=True)
    caps_name   = Column(String(50))

class Character(Base):
    __tablename__ = 'characters'
    id          = Column(Integer, primary_key=True)
    name        = Column(String(50))

    def _indirect_name(self, value):
        self.name = value
    indirect_name = property(None, _indirect_name)
