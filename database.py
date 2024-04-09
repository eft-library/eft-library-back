from sqlalchemy import create_engine, text, URL
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import urllib.parse


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
            password=urllib.parse.quote_plus(os.getenv("DB_PASSWORD")),
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            port=os.getenv("DB_PORT")
        )

        engine = create_engine(url_object)
        session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return session()
