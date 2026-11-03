"""S3-compatible client configuration for RustFS community uploads."""
import os
from urllib.parse import urlsplit

from minio import Minio


def create_object_storage_client():
    endpoint = os.getenv('RUSTFS_ENDPOINT')
    if not endpoint:
        raise ValueError('RUSTFS_ENDPOINT is required')
    parsed = urlsplit(endpoint if '://' in endpoint else 'http://' + endpoint)
    if (parsed.scheme not in ('http', 'https') or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
        raise ValueError('Object storage endpoint must be an HTTP(S) host with optional port')
    access_key = os.getenv('RUSTFS_ACCESS_KEY')
    secret_key = os.getenv('RUSTFS_SECRET_KEY')
    if not access_key or not secret_key:
        raise ValueError('RUSTFS_ACCESS_KEY and RUSTFS_SECRET_KEY are required')
    return Minio(parsed.netloc, access_key=access_key,
                 secret_key=secret_key, secure=parsed.scheme == 'https')
