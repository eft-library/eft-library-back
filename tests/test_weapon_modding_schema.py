"""Validate additive modding DDL, source edge cases and multi-level traversal in PostgreSQL."""
import importlib.util
import re
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

ROOT = Path(__file__).parents[1]
TABLES = (
    'item_categories', 'item_category_memberships', 'item_slots',
    'item_slot_item_filters', 'item_slot_category_filters', 'item_conflicting_items',
    'item_conflicting_slots', 'item_conflicting_categories', 'item_mod_properties',
    'item_presets', 'weapon_preset_links', 'item_preset_components',
)


@unittest.skipUnless(importlib.util.find_spec('pgserver'), 'Install pgserver for isolated PostgreSQL tests')
class WeaponModdingSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pgserver
        directory = tempfile.TemporaryDirectory(prefix='weapon-modding-')
        cls.addClassCleanup(directory.cleanup)
        server = pgserver.get_server(Path(directory.name) / 'postgres', cleanup_mode='delete')
        cls.addClassCleanup(server.cleanup)
        cls.engine = create_engine(server.get_uri())
        cls.addClassCleanup(cls.engine.dispose)
        cls.schema = (ROOT / 'platform_db.sql').read_text()
        cls.migration = (ROOT / 'sql/migrations/20261110_weapon_modding.sql').read_text()
        with cls.engine.begin() as conn:
            for name in ('items', 'weapon_items'):
                ddl = re.search(rf'create table if not exists {name}\s*\(.*?\n\);', cls.schema, re.S).group()
                conn.exec_driver_sql(ddl)
            conn.exec_driver_sql("insert into items(id,name_en) values ('existing','Preserved')")
        raw = cls.engine.raw_connection()
        try:
            with raw.cursor() as cursor:
                cursor.execute(cls.migration)
                cursor.execute(cls.migration)
            raw.commit()
        finally:
            raw.close()

    def setUp(self):
        self.conn = self.engine.connect()
        self.addCleanup(self.conn.close)
        transaction = self.conn.begin()
        self.addCleanup(transaction.rollback)
        self.conn.exec_driver_sql("""
            insert into items(id) values ('gun'),('receiver'),('sight'),('scope'),('preset');
            insert into weapon_items(item_id) values ('gun');
            insert into item_categories(id) values ('mods');
            insert into item_slots(item_id,slot_id,name_id,required,sort_order) values
                ('gun','receiver-slot','mod_reciever',true,0),
                ('receiver','rear-slot','mod_sight_rear',false,0);
            insert into item_slot_item_filters values
                ('gun','receiver-slot','allowed','receiver',0),
                ('receiver','rear-slot','allowed','sight',0);
            insert into item_presets(preset_item_id,base_item_id,is_default) values
                ('preset','gun',true);
        """)

    def test_migration_is_additive_repeatable_and_matches_authoritative_schema(self):
        self.assertEqual(self.conn.exec_driver_sql("select name_en from items where id='existing'").scalar_one(), 'Preserved')
        for table in TABLES:
            pattern = rf'create table if not exists {table}\s*\(.*?\n\);'
            self.assertEqual(re.search(pattern,self.schema,re.S).group(),
                             re.search(pattern,self.migration,re.S).group())
            self.assertIsNotNone(self.conn.execute(text('select to_regclass(:name)'), {'name':table}).scalar_one())
        # Check all indexes and COMMENT statements as well, rather than table definitions only.
        start = self.schema.index('-- 총기 모딩 원천 관계.')
        end = self.schema.index('create table if not exists ammo_items (',start)
        block = self.schema[start:end].strip()
        self.assertIn(block,self.migration)

    def test_multi_level_mounting_path_and_category_conditions(self):
        rows = self.conn.exec_driver_sql("""
            with recursive paths(item_id, visited) as (
                select 'gun'::text, array['gun']::text[]
                union all
                select f.target_item_id, p.visited || f.target_item_id
                from paths p join item_slots s on s.item_id=p.item_id
                join item_slot_item_filters f on f.item_id=s.item_id and f.slot_id=s.slot_id
                where f.filter_type='allowed' and not f.target_item_id=any(p.visited)
            ) select visited from paths where item_id='sight'
        """).scalar_one()
        self.assertEqual(rows, ['gun','receiver','sight'])
        self.conn.exec_driver_sql("""
            insert into item_category_memberships values ('sight','mods',0);
            insert into item_slot_category_filters values
                ('receiver','rear-slot','allowed','mods',0),
                ('receiver','rear-slot','excluded','mods',0);
        """)
        self.assertEqual(self.conn.exec_driver_sql('select count(*) from item_slot_category_filters').scalar_one(),2)

    def test_unresolved_conflict_slot_and_direction_are_preserved(self):
        self.conn.exec_driver_sql("""
            insert into item_conflicting_slots values ('sight','missing-source-slot',0);
            insert into item_conflicting_items values ('sight','receiver',0);
        """)
        self.assertEqual(self.conn.exec_driver_sql('select conflicting_slot_id from item_conflicting_slots').scalar_one(),'missing-source-slot')
        self.assertEqual(self.conn.exec_driver_sql("select count(*) from item_conflicting_items where item_id='receiver'").scalar_one(),0)

    def test_components_preserve_repetition_attributes_and_no_mount_location(self):
        self.conn.exec_driver_sql("""
            insert into item_preset_components values
                ('preset',0,'sight',1,'{"nested":{"value":[1,2]}}'),
                ('preset',1,'sight',2,'{}');
        """)
        rows = self.conn.exec_driver_sql('select quantity,attributes from item_preset_components order by component_index').all()
        self.assertEqual(rows, [(1,{'nested':{'value':[1,2]}}),(2,{})])
        self.conn.exec_driver_sql("delete from item_presets where preset_item_id='preset'")
        self.assertEqual(self.conn.exec_driver_sql('select count(*) from item_preset_components').scalar_one(),0)

    def test_default_reference_is_distinct_from_preset_flag_and_unique(self):
        self.conn.exec_driver_sql("""
            update item_presets set is_default=false where preset_item_id='preset';
            insert into weapon_preset_links values ('gun','preset',false,true,null);
            insert into items(id) values ('other-preset');
            insert into item_presets(preset_item_id,base_item_id,is_default) values ('other-preset','gun',false);
        """)
        with self.assertRaises(IntegrityError), self.conn.begin_nested():
            self.conn.exec_driver_sql("insert into weapon_preset_links values ('gun','other-preset',true,true,0)")
        self.conn.exec_driver_sql("insert into weapon_preset_links values ('gun','other-preset',true,false,0)")
        self.assertEqual(self.conn.exec_driver_sql('select count(*) from weapon_preset_links').scalar_one(),2)
        self.assertFalse(self.conn.exec_driver_sql("select is_default from item_presets where preset_item_id='preset'").scalar_one())

    def test_source_filter_and_conflict_duplicates_keep_array_positions(self):
        self.conn.exec_driver_sql("""
            insert into item_slot_item_filters values ('gun','receiver-slot','allowed','receiver',1);
            insert into item_conflicting_items values ('sight','receiver',0),('sight','receiver',1);
        """)
        self.assertEqual(self.conn.exec_driver_sql("select count(*) from item_slot_item_filters where item_id='gun'").scalar_one(),2)
        self.assertEqual(self.conn.exec_driver_sql('select count(*) from item_conflicting_items').scalar_one(),2)
        with self.assertRaises(IntegrityError), self.conn.begin_nested():
            self.conn.exec_driver_sql("insert into item_slot_item_filters values ('gun','receiver-slot','allowed','sight',1)")

    def test_modifiers_keep_source_scale_and_nested_zoom(self):
        self.conn.exec_driver_sql("""
            insert into item_mod_properties(item_id,properties_type,recoil_modifier,item_recoil_modifier,zoom_levels)
            values ('scope','ItemPropertiesScope',-0.01,-1,'[[1,4],[2.5]]');
        """)
        row=self.conn.exec_driver_sql('select recoil_modifier,item_recoil_modifier,zoom_levels,ergonomics from item_mod_properties').one()
        self.assertEqual(float(row[0]),-0.01)
        self.assertEqual(float(row[1]),-1)
        self.assertEqual(row[2],[[1,4],[2.5]])
        self.assertIsNone(row[3])
        with self.assertRaises(IntegrityError), self.conn.begin_nested():
            self.conn.exec_driver_sql("update item_mod_properties set zoom_levels='{}'")

    def test_foreign_keys_and_slot_filter_cascade(self):
        with self.assertRaises(IntegrityError), self.conn.begin_nested():
            self.conn.exec_driver_sql("insert into item_slot_item_filters values ('gun','receiver-slot','allowed','missing-item',1)")
        self.conn.exec_driver_sql("delete from item_slots where item_id='receiver'")
        self.assertEqual(self.conn.exec_driver_sql("select count(*) from item_slot_item_filters where item_id='receiver'").scalar_one(),0)
        with self.assertRaises(IntegrityError), self.conn.begin_nested():
            self.conn.exec_driver_sql("insert into item_slot_item_filters values ('gun','receiver-slot','invalid','sight',1)")
