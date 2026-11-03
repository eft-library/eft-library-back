"""Validate deferred ORM references without connecting to the database."""
import unittest

from sqlalchemy.orm import configure_mappers


class ModelMappingTest(unittest.TestCase):
    def test_application_models_initialize(self):
        # Loading the application routers registers the models used by endpoints.
        import api.router  # noqa: F401

        configure_mappers()
