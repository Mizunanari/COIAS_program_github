from sqlalchemy import Column, Integer, DateTime
from database import Base


class Pdr3AllCOIASImages(Base):
    __tablename__ = 'pdr3_all_COIAS_images'

    image_id = Column(Integer(),  primary_key=True, nullable=False, autoincrement=True)
    image_name = Column(Integer(), nullable=False)
    url = Column(Integer(), nullable=True)
    observe_date = Column(Integer(), nullable=True)
    jd = Column(Integer(), nullable=True)
    ra_patch = Column(Integer(), nullable=True)
    dec_patch = Column(Integer(), nullable=True)
    version = Column(Integer(), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return "<Pdr3AllCOIASImages %r>" % self.__class__
