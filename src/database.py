from sqlalchemy import create_engine, text, URL
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os


class DataBaseConnector:
    """
    Database 연결 후 ORM 사용
    """
    @classmethod
    def create_session(cls):
        load_dotenv()

        url_object = URL.create(
            "postgresql+psycopg2",
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
        )

        engine = create_engine(url_object)
        session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return session()

    @classmethod
    def close_session(cls, session):
        session.close()
