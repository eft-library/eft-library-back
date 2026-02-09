from database import DataBaseConnector
import logging
from api.story.models import Story, StoryRoadmap

logger = logging.getLogger("api.story")


class StoryServices:

    @staticmethod
    def get_story_by_id(story_id: str):
        try:
            with DataBaseConnector.SessionLocal() as s:
                selector_list = (
                    s.query(Story.id, Story.name).order_by(Story.order).all()
                )
                selector_list_result = [
                    {"id": id, "name": name} for id, name in selector_list
                ]

                story_detail = s.query(Story).filter(Story.id == story_id).first()
                detail_data = {"selector": selector_list_result, "detail": story_detail}
                return detail_data
        except Exception as e:
            logger.error(
                f"get_story_by_id error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_story_roadmap():
        try:
            with DataBaseConnector.SessionLocal() as s:
                story_roadmap_list = s.query(StoryRoadmap).all()
                return story_roadmap_list
        except Exception as e:
            logger.error(
                f"get_story_roadmap error: {e}",
                exc_info=True,
            )
            return None
