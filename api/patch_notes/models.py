from database import DataBaseConnector
from sqlalchemy import Column, String, ARRAY, TEXT, TIMESTAMP


class PatchNotes(DataBaseConnector.Base):
    """
    PatchNotes
    """

    __tablename__ = "tkl_patch_notes"

    id = Column("id", TEXT, primary_key=True)
    name_en = Column(String)
    name_kr = Column(String)
    notes_en = Column(TEXT)
    notes_kr = Column(TEXT)
    update_time = Column(TIMESTAMP)
