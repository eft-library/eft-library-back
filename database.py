from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from sqlalchemy.ext.declarative import declarative_base


class DataBaseConnector:
    """
    Database 연결 후 ORM 사용
    """
    Base = declarative_base()
    @classmethod
    def create_session(cls):
        load_dotenv()
        url_object = URL.create(
            "postgresql+psycopg2",
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            port=os.getenv("DB_PORT")
        )

        engine = create_engine(url_object)
        session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return session()

    @classmethod
    def get_base(cls):
        return cls.Base
