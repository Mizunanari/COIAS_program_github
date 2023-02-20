from sqlalchemy import Column, Integer, Text, Float
from API.database import Base


class ImageInfo(Base):
    __tablename__ = 'image_info'

    image_id = Column(Integer(),  primary_key=True, nullable=False, autoincrement=True)
    image_name = Column(Text(), nullable=False)
    direct_parent_dir_id = Column(Text(), nullable=True)
    full_dir = Column(Text(), nullable=True)
    observe_date = Column(Text(),  primary_key=True, nullable=False)
    observe_time = Column(Float(), nullable=False)
    jd = Column(Float(), nullable=True)
    ra_tract = Column(Float(), nullable=True)
    dec_tract = Column(Float(), nullable=True)
    ra_patch_center = Column(Float(), nullable=True)
    dec_patch_center = Column(Float(), nullable=True)
    ra_patch_lowest = Column(Float(),  primary_key=True, nullable=False)
    dec_patch_lowest = Column(Float(), nullable=False)
    ra_patch_highest = Column(Float(), nullable=True)
    dec_patch_highest = Column(Float(), nullable=True)
    tract_patch = Column(Text(), nullable=True)
    filter = Column(Text(), nullable=True)
    exposure_time = Column(Float(), nullable=True)
    is_auto_measured = Column(Integer(),   nullable=False)
    measurer_uid = Column(Text(), nullable=False)
    is_manual_measured = Column(Integer(), nullable=True)

    def __repr__(self): 
        return "<ImageInfo %r>" % self.__class__
        