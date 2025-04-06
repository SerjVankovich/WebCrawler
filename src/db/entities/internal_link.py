from sqlalchemy import Column, Integer, Text

from src.db.base import Base

class InternalLink(Base):
    __tablename__ = 'internal_links'

    id = Column(Integer, primary_key=True)
    url = Column(Text, unique=True, nullable=False)
    count = Column(Integer, default=0)