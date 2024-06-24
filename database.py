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
    def create_engine(cls):
        url_object = URL.create(
            drivername="postgresql+psycopg2",
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            port=os.getenv("DB_PORT"),
        )
        engine = create_engine(url_object, echo=True)
        return engine

    # 세션 팩토리 생성
    @classmethod
    def create_session_factory(cls):
        engine = cls.create_engine()
        session = sessionmaker(bind=engine)
        return session
