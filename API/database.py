from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import API.config as config

host_ip = config.MYSQL_HOST
host_port = config.MYSQL_PORT
db_name = config.MYSQL_DATABASE_NAME
username = config.MYSQL_USER_NAME
password = config.MYSQL_PASSWORD

DATABASE = f"mysql+pymysql://{username}:{password}@{host_ip}:{host_port}/{db_name}?charset=utf8mb4"

ENGINE = create_engine(
    DATABASE,
    echo=True,
    pool_size=10,
    max_overflow=29
)

session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=ENGINE
    )
)

Base = declarative_base()
Base.query = session.query_property()