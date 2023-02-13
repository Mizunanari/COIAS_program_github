from sqlalchemy import Column, Integer, Text, Float
from database import Base


class DirStructure(Base):
    __tablename__ = 'dir_structure'

    this_dir_id = Column(Integer(),  primary_key=True, nullable=False, autoincrement=True)
    this_dir_name = Column(Text(), nullable=False)
    level = Column(Integer(), nullable=True)
    parent_dir_id = Column(Integer(), nullable=True)
    parent_dir_name = Column(Text(), nullable=True)
    is_ecliptic = Column(Float(), nullable=True)
    ra_lowest = Column(Integer(), nullable=True)
    dec_lowest = Column(Float(),  primary_key=True, nullable=False, autoincrement=True)
    ra_highest = Column(Float(), nullable=False)
    dec_highest = Column(Float(), nullable=True)
    n_total_images = Column(Integer(), nullable=True)
    n_measured_images = Column(Integer(), nullable=True)

    def __repr__(self):
        return "<DirStructure %r>" % self.__class__
