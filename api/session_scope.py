from database import DataBaseConnector
from contextlib import contextmanager


class SessionManger:
    @staticmethod
    @contextmanager
    def session_scope():
        """
        컨택스트 관리자를 통한 세션 관리
        """
        session = DataBaseConnector.create_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
