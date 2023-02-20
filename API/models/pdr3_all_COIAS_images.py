from sqlalchemy import Column, Integer, Text, Float
from API.database import Base


class Pdr3AllCOIASImages(Base):
    __tablename__ = 'pdr3_all_COIAS_images'

    image_id = Column(Integer(),  primary_key=True, nullable=False, autoincrement=True)
    image_name = Column(Text(), nullable=False)
    url = Column(Text(), nullable=True)
    observe_date = Column(Text(), nullable=True)
    jd = Column(Float(), nullable=True)
    ra_patch = Column(Float(), nullable=True)
    dec_patch = Column(Float(), nullable=True)

    def __repr__(self):
        return "<Pdr3AllCOIASImages %r>" % self.__class__
