from sqlalchemy import Column, Integer, Text, Float, DECIMAL
from API.database import Base


class MeasureResult(Base):
    __tablename__ = 'measure_result'

    this_measure_id = Column(Integer(), primary_key=True, nullable=False, autoincrement=True)
    measured_image_id = Column(Integer(), nullable=True)
    measurer_uid = Column(Integer(),  primary_key=True, nullable=False)
    final_all_txt_name = Column(Text(), nullable=False)
    measure_date = Column(Text(), nullable=True)
    aparture_radius = Column(Integer(), nullable=True)
    final_all_one_line = Column(Text(), nullable=True)
    object_name = Column(Text(), nullable=True)
    ra_deg = Column(Float(), nullable=True)
    dec_deg = Column(Float(),  primary_key=True, nullable=False)
    mag = Column(DECIMAL(5, 3), nullable=False)
    mag_err = Column(DECIMAL(5, 3), nullable=True)
    x_pix = Column(DECIMAL(5, 3), nullable=True)
    y_pix = Column(DECIMAL(5, 3), nullable=True)
    is_auto = Column(Integer(), nullable=True)
    observation_arc = Column(Text(), nullable=True)
    work_dir = Column(Text(),   nullable=False)

    def __repr__(self):
        return "<MeasureResult %r>" % self.__class__