from sqlalchemy import Column, Integer, Text

from src.db.base import Base

class ExternalDomain(Base):
    __tablename__ = 'external_domains'

    id = Column(Integer, primary_key=True)
    domain = Column(Text, unique=True, nullable=False)
    count = Column(Integer, default=0)