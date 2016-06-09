from .test_base import Base
from sqlalchemy import Column, Integer, String


class Account(Base):
    __tablename__ = 'accounts'
    id          = Column(Integer, primary_key=True)
    name        = Column(String(50), unique=True)
    owner       = Column(String(50), unique=True)
