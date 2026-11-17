"""Destructive migration preserves shared maps/routes and rejects unrelated assets."""
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from scripts.retire_3d_map_assets import load_objects, DEFAULT_MANIFEST
from api.map.models import Map

ROOT=Path(__file__).parents[1]


class AssetManifestTests(unittest.TestCase):
    def test_captured_objects_are_unique_and_other_folders_are_rejected(self):
        objects=load_objects(DEFAULT_MANIFEST)
        self.assertEqual(len(objects),18)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'manifest.json'
            for key in ('tkl_community/posts_image/photo.glb','tkl_map/../photo.glb','tkl_map/photo.png'):
                path.write_text(json.dumps({'objects':[{'bucket':'eftlibrary','key':key,'url':'https://image.eftlibrary.com/eftlibrary/'+key}]}))
                with self.assertRaises(ValueError):load_objects(path)

    def test_only_3d_route_is_retired(self):
        from api.router import api_router
        paths={route.path for route in api_router.routes}
        self.assertNotIn('/map/v3/detail/{normalized_name}',paths)
        self.assertIn('/map-of-tarkov/v3/detail/{normalized_name}',paths)
        self.assertIn('/live-map/v3/detail/{normalized_name}',paths)


@unittest.skipUnless(importlib.util.find_spec('pgserver'),'pgserver required')
class RetireMapMigrationTests(unittest.TestCase):
    def test_repeated_drop_keeps_map_rows_and_non_3d_links(self):
        import pgserver
        with tempfile.TemporaryDirectory() as directory:
            server=pgserver.get_server(Path(directory)/'db',cleanup_mode='delete')
            engine=create_engine(server.get_uri())
            try:
                schema=(ROOT/'platform_db.sql').read_text()
                with engine.begin() as conn:
                    for name in ('maps','autocomplete_items','sitemap','menu_sub_groups'):
                        conn.exec_driver_sql(re.search(rf'create table if not exists {name}\s*\(.*?\n\);',schema,re.S).group())
                    conn.exec_driver_sql("alter table maps add column three_image text,add column three_json jsonb")
                    conn.exec_driver_sql("insert into maps(id,normalized_name,mot_image_en,three_image,three_json) values ('shared','customs','2d.png','3d.glb','[]')")
                    for table in ('autocomplete_items','sitemap','menu_sub_groups'):
                        for i,url in enumerate(('/map','/map/customs','https://eftlibrary.com/map/woods','/map-of-tarkov/customs','/live-map/customs','/roadmap','/maple','https://example.com/map/customs')):
                            if table=='menu_sub_groups':conn.execute(text('insert into menu_sub_groups(id,url) values (:id,:url)'),{'id':str(i),'url':url})
                            else:conn.execute(text(f'insert into {table}(url) values (:url)'),{'url':url})
                raw=engine.raw_connection()
                try:
                    with raw.cursor() as cursor:
                        sql=(ROOT/'sql/migrations/20261118_retire_3d_maps.sql').read_text()
                        cursor.execute(sql);cursor.execute(sql)
                    raw.commit()
                finally:raw.close()
                with Session(engine) as session:
                    record=session.get(Map,'shared')
                    self.assertEqual(record.mot_image_en,'2d.png')
                    self.assertEqual(record.normalized_name,'customs')
                    self.assertNotIn('three_image',Map.__table__.columns)
                    for table in ('autocomplete_items','sitemap','menu_sub_groups'):
                        urls=set(session.execute(text(f'select url from {table}')).scalars())
                        self.assertEqual(urls,{'/map-of-tarkov/customs','/live-map/customs','/roadmap','/maple','https://example.com/map/customs'})
            finally:
                engine.dispose();server.cleanup()
