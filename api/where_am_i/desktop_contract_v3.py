"""Shared desktop contract values, independent of web-map database identities."""
import re
from urllib.parse import unquote, urlsplit

VERSION_PATTERN_V3 = r'[0-9]+(?:\.[0-9]+){1,3}'


def version_parts_v3(value):
    if not isinstance(value, str) or len(value) > 64 or not re.fullmatch(VERSION_PATTERN_V3, value):
        raise ValueError('Version must contain 2 to 4 numeric components')
    parts_v3 = tuple(int(part_v3) for part_v3 in value.split('.'))
    if any(part_v3 > 2147483647 for part_v3 in parts_v3):
        raise ValueError('Version component exceeds .NET Int32 range')
    return parts_v3 + (0,) * (4 - len(parts_v3))


def normalize_alias_v3(value):
    normalized_v3 = value.strip().lower().replace('_preset', '')
    if not re.fullmatch(r'[a-z0-9 _-]{1,128}', normalized_v3):
        raise ValueError('Invalid map alias')
    return normalized_v3


def validate_download_url_v3(value):
    if (not isinstance(value, str) or len(value) > 4096
            or any(character_v3.isspace() or ord(character_v3) < 32 or ord(character_v3) == 127
                   for character_v3 in value)):
        raise ValueError('Invalid download URL')
    parsed_v3 = urlsplit(value)
    if (parsed_v3.scheme != 'https'
            or parsed_v3.port not in (None, 443) or parsed_v3.username is not None
            or parsed_v3.password is not None or '\\' in value):
        raise ValueError('Unsupported download URL')
    if parsed_v3.hostname in ('eftlibrary.com', 'www.eftlibrary.com'):
        return value
    path_v3 = unquote(parsed_v3.path)
    release_path_v3 = '/eft-library/eft-library-where-am-i/releases'
    if (parsed_v3.hostname != 'github.com'
            or not (path_v3.lower() == release_path_v3 or path_v3.lower().startswith(release_path_v3 + '/'))
            or any(part_v3 in ('.', '..') for part_v3 in path_v3.split('/'))
            or '\\' in path_v3 or any(ord(character_v3) < 32 for character_v3 in path_v3)):
        raise ValueError('Unsupported download URL')
    return value
