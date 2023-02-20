from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import API.config as config

host_ip = config.DB_HOST
host_port = config.DB_PORT
db_name = config.DB_DATABASE_NAME
username = config.DB_USER_NAME
password = config.DB_PASSWORD

DATABASE = f"mysql+pymysql://{username}:{password}@{host_ip}:{host_port}/{db_name}?charset=utf8"

print(DATABASE)

ENGINE = create_engine(
    DATABASE,
    echo=True,
    pool_size=10,
    max_overflow=29,
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