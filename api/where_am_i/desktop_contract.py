"""Shared desktop contract values, independent of web-map database identities."""
import re
from urllib.parse import unquote, urlsplit

VERSION_PATTERN = r'[0-9]+(?:\.[0-9]+){1,3}'


def version_parts(value):
    if not isinstance(value, str) or len(value) > 64 or not re.fullmatch(VERSION_PATTERN, value):
        raise ValueError('Version must contain 2 to 4 numeric components')
    parts = tuple(int(part) for part in value.split('.'))
    if any(part > 2147483647 for part in parts):
        raise ValueError('Version component exceeds .NET Int32 range')
    return parts + (0,) * (4 - len(parts))


def normalize_alias(value):
    normalized = value.strip().lower().replace('_preset', '')
    if not re.fullmatch(r'[a-z0-9 _-]{1,128}', normalized):
        raise ValueError('Invalid map alias')
    return normalized


def validate_download_url(value):
    if (not isinstance(value, str) or len(value) > 4096
            or any(character.isspace() or ord(character) < 32 or ord(character) == 127
                   for character in value)):
        raise ValueError('Invalid download URL')
    parsed = urlsplit(value)
    if (parsed.scheme != 'https'
            or parsed.port not in (None, 443) or parsed.username is not None
            or parsed.password is not None or '\\' in value):
        raise ValueError('Unsupported download URL')
    if parsed.hostname in ('eftlibrary.com', 'www.eftlibrary.com'):
        return value
    path = unquote(parsed.path)
    release_path = '/eft-library/eft-library-where-am-i/releases'
    if (parsed.hostname != 'github.com'
            or not (path.lower() == release_path or path.lower().startswith(release_path + '/'))
            or any(part in ('.', '..') for part in path.split('/'))
            or '\\' in path or any(ord(character) < 32 for character in path)):
        raise ValueError('Unsupported download URL')
    return value
