from database import V3Database
import logging
from api.story.models import StoryRoadmapV3, StoryV3

logger = logging.getLogger("api.story")


class StoryServiceV3:
    @staticmethod
    def _serialize_story_selector_v3(story: StoryV3):
        return {
            "id": story.id,
            "title_en": story.title_en,
            "title_ko": story.title_ko,
            "title_ja": story.title_ja,
        }

    @staticmethod
    def _serialize_story_detail_v3(story: StoryV3):
        return {
            "id": story.id,
            "title_en": story.title_en,
            "title_ko": story.title_ko,
            "title_ja": story.title_ja,
            "objectives_en": story.objectives_en,
            "objectives_ko": story.objectives_ko,
            "objectives_ja": story.objectives_ja,
            "requirements_en": story.requirements_en,
            "requirements_ko": story.requirements_ko,
            "requirements_ja": story.requirements_ja,
            "guide_en": story.guide_en,
            "guide_ko": story.guide_ko,
            "guide_ja": story.guide_ja,
            "update_time": story.update_time,
        }

    @staticmethod
    def _serialize_story_roadmap_v3(roadmap: StoryRoadmapV3):
        return {
            "id": roadmap.id,
            "node_type": roadmap.node_type,
            "title_en": roadmap.title_en,
            "title_ko": roadmap.title_ko,
            "title_ja": roadmap.title_ja,
            "contents_en": roadmap.contents_en,
            "contents_ko": roadmap.contents_ko,
            "contents_ja": roadmap.contents_ja,
            "desc_en": roadmap.desc_en,
            "desc_ko": roadmap.desc_ko,
            "desc_ja": roadmap.desc_ja,
            "value_text": roadmap.value_text,
            "image": roadmap.image,
            "x_coordinate": (
                float(roadmap.x_coordinate)
                if roadmap.x_coordinate is not None
                else None
            ),
            "y_coordinate": (
                float(roadmap.y_coordinate)
                if roadmap.y_coordinate is not None
                else None
            ),
            "edge": roadmap.edge,
            "update_time": roadmap.update_time,
        }

    @staticmethod
    def get_story_by_id_v3(story_id: str):
        try:
            with V3Database.SessionLocal() as s:
                selector_list = s.query(StoryV3).order_by(StoryV3.sort_order).all()
                story_detail = s.query(StoryV3).filter(StoryV3.id == story_id).first()

                return {
                    "selector": [
                        StoryServiceV3._serialize_story_selector_v3(story)
                        for story in selector_list
                    ],
                    "detail": (
                        StoryServiceV3._serialize_story_detail_v3(story_detail)
                        if story_detail is not None
                        else None
                    ),
                }
        except Exception as e:
            logger.error(
                f"get_story_by_id_v3 error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_story_roadmap_v3():
        try:
            with V3Database.SessionLocal() as s:
                story_roadmap_list = (
                    s.query(StoryRoadmapV3)
                    .order_by(StoryRoadmapV3.node_type, StoryRoadmapV3.id)
                    .all()
                )
                return [
                    StoryServiceV3._serialize_story_roadmap_v3(roadmap)
                    for roadmap in story_roadmap_list
                ]
        except Exception as e:
            logger.error(
                f"get_story_roadmap_v3 error: {e}",
                exc_info=True,
            )
            return None
