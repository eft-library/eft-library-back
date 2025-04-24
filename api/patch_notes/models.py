from database import DataBaseConnector
from sqlalchemy import Column, JSON, TEXT, TIMESTAMP


class PatchNotes(DataBaseConnector.Base):
    """
    PatchNotes
    """

    __tablename__ = "patch_notes_i18n"

    id = Column("id", TEXT, primary_key=True)
    name = Column(JSON)
    description = Column(JSON)
    update_time = Column(TIMESTAMP)
