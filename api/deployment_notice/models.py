from sqlalchemy import BOOLEAN, TEXT, TIMESTAMP, Column

from database import V3Database


class DeploymentNoticeV3(V3Database.Base):
    __tablename__ = "deployment_notice"

    id = Column(TEXT, primary_key=True)
    is_active = Column(BOOLEAN)
    message_ko = Column(TEXT)
    message_en = Column(TEXT)
    message_ja = Column(TEXT)
    start_time = Column(TIMESTAMP)
    end_time = Column(TIMESTAMP)
    updated_by = Column(TEXT)
    update_time = Column(TIMESTAMP)
