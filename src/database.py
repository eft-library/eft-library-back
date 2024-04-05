from sqlalchemy import create_engine, text, URL
from dotenv import load_dotenv
import os


class DataBaseConnector:
    """
    Database 연결 후 쿼리 전송
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
            return conn.execute(text(query))

# 사용 방법
# result = DataBaseConnector.query_sender('select * from v_api2_incident_api')
# rows = [row for row in result]
#
# print(rows)

