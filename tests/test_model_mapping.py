"""Validate deferred ORM references without connecting to the database."""
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, configure_mappers


class ModelMappingTest(unittest.TestCase):
    def test_application_models_initialize(self):
        # Loading the application routers registers the models used by endpoints.
        import api.router  # noqa: F401

        configure_mappers()

    def test_menu_relationship_loads_in_sort_order(self):
        from api.home.models import MenuGroup, MenuSubGroup

        engine = create_engine("sqlite://")
        self.addCleanup(engine.dispose)
        MenuGroup.__table__.create(engine)
        MenuSubGroup.__table__.create(engine)
        with Session(engine) as session:
            session.add(MenuGroup(id="menu"))
            session.add_all([
                MenuSubGroup(id="second", parent_group_id="menu", sort_order=2),
                MenuSubGroup(id="first", parent_group_id="menu", sort_order=1),
            ])
            session.commit()
            session.expire_all()
            menu = session.get(MenuGroup, "menu")
            self.assertEqual([child.id for child in menu.sub_menus], ["first", "second"])
            self.assertIs(menu.sub_menus[0].main_menu, menu)
