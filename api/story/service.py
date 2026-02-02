from database import DataBaseConnector
import logging
from api.story.models import Story

logger = logging.getLogger("api.story")


class StoryServices:
    @staticmethod
    def get_story_selector():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                selector_list = (
                    s.query(Story.id, Story.name).order_by(Story.order).all()
                )
                selector_list_result = [
                    {"id": id, "name": name} for id, name in selector_list
                ]
                return selector_list_result
        except Exception as e:
            logger.error(
                f"get_story_selector error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_story_by_id(story_id: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                story_detail = s.query(Story).filter(Story.id == story_id).first()
                return story_detail
        except Exception as e:
            logger.error(
                f"get_story_by_id error: {e}",
                exc_info=True,
            )
            return None
