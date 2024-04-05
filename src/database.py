from sqlalchemy import create_engine, text, URL
from dotenv import load_dotenv
import os


class DataBaseConnector:
    """
    Database 연결 후 쿼리 전송
    결과를 tuple List에 담아서 반환 => [(1, a, 2), (2, b, 3)]
    orm을 사용하지 않고 쿼리를 직접 작성할 것이기에 session 미사용
    """
    @classmethod
    def query_sender(cls, query):
        load_dotenv()

        url_object = URL.create(
            "postgresql+psycopg2",
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
        )

        engine = create_engine(url_object)

        with engine.connect() as conn:
            result = conn.execute(text(query))
            return [row for row in result]


