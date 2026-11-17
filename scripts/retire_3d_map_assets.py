"""Delete only the captured 3D GLB objects, after deployment and column removal."""
import argparse
import json
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DEFAULT_MANIFEST = ROOT/'sql/migrations/20261118_retire_3d_maps.assets.json'


def load_objects(path):
    manifest = json.loads(Path(path).read_text())
    objects = []
    seen = set()
    for row in manifest['objects']:
        bucket, key = row['bucket'], row['key']
        parsed = urlsplit(row['url'])
        if (bucket != 'eftlibrary' or not key.startswith('tkl_map/') or not key.endswith('.glb')
                or any(part in ('', '.', '..') for part in key.split('/'))
                or parsed.scheme != 'https' or parsed.netloc != 'image.eftlibrary.com'
                or parsed.query or parsed.fragment or unquote(parsed.path) != f'/{bucket}/{key}'):
            raise ValueError('Manifest contains an unexpected object')
        if (bucket, key) in seen:
            raise ValueError('Duplicate manifest object')
        seen.add((bucket, key))
        objects.append((bucket, key))
    if not objects:
        raise ValueError('Empty manifest')
    return objects


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--execute', action='store_true', help='Remove exact objects after schema retirement')
    args = parser.parse_args()
    objects = load_objects(args.manifest)
    if not args.execute:
        for bucket, key in objects:
            print(f'Would delete: {bucket}/{key}')
        print(f'Dry run: {len(objects)} objects. No database or storage changes.')
        return

    from dotenv import load_dotenv
    from sqlalchemy import text
    load_dotenv(ROOT/'.env')
    from database import Database
    from util.object_storage import create_object_storage_client
    with Database.SessionLocal() as session:
        session.execute(text('SET TRANSACTION READ ONLY'))
        remaining = session.execute(text("""select count(*) from information_schema.columns
            where table_schema=current_schema() and table_name='maps'
              and column_name in ('three_image','three_json')""")).scalar_one()
        if remaining:
            raise RuntimeError('Deploy the API changes and apply 20261118_retire_3d_maps.sql first')
        if session.execute(text('select to_regclass(\'maps\')')).scalar_one() is None:
            raise RuntimeError('Expected maps table is missing')

    from minio.error import S3Error
    client = create_object_storage_client()
    pending = []
    # Check all objects/permissions before beginning deletions. No bucket-prefix deletion.
    for bucket, key in objects:
        try:
            client.stat_object(bucket, key)
            pending.append((bucket, key))
        except S3Error as exc:
            if exc.code not in ('NoSuchKey', 'NoSuchObject'):
                raise
            print(f'Already absent: {bucket}/{key}')
    for bucket, key in pending:
        client.remove_object(bucket, key)
        print(f'Deleted: {bucket}/{key}')
    print(f'Deleted {len(pending)} objects. The operation can be retried for remaining objects.')


if __name__ == '__main__':
    main()
