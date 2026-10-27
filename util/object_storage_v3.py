"""S3-compatible client configuration for RustFS community uploads."""
import os
from urllib.parse import urlsplit

from minio import Minio


def create_object_storage_client_v3():
    endpoint_v3 = os.getenv('RUSTFS_ENDPOINT')
    if not endpoint_v3:
        raise ValueError('RUSTFS_ENDPOINT is required')
    parsed_v3 = urlsplit(endpoint_v3 if '://' in endpoint_v3 else 'http://' + endpoint_v3)
    if (parsed_v3.scheme not in ('http', 'https') or not parsed_v3.hostname
            or parsed_v3.username is not None or parsed_v3.password is not None
            or parsed_v3.path not in ('', '/') or parsed_v3.query or parsed_v3.fragment):
        raise ValueError('Object storage endpoint must be an HTTP(S) host with optional port')
    access_key_v3 = os.getenv('RUSTFS_ACCESS_KEY')
    secret_key_v3 = os.getenv('RUSTFS_SECRET_KEY')
    if not access_key_v3 or not secret_key_v3:
        raise ValueError('RUSTFS_ACCESS_KEY and RUSTFS_SECRET_KEY are required')
    return Minio(parsed_v3.netloc, access_key=access_key_v3,
                 secret_key=secret_key_v3, secure=parsed_v3.scheme == 'https')
