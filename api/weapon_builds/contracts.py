"""OpenAPI contracts shared by user build routes; runtime errors use HttpError."""
from api.weapon_builds.schemas import BuildError
from util.http_exceptions import HttpError


def error_responses(*errors: HttpError, authentication: bool = False):
    definitions = [HttpError.BUILD_STORAGE_UNAVAILABLE, *errors]
    if authentication:
        definitions += [HttpError.LOGIN_REQUIRED, HttpError.INVALID_TOKEN,
                        HttpError.AUTH_SERVICE_UNAVAILABLE, HttpError.BUILD_REGISTERED_USER_REQUIRED]
    grouped = {}
    for error in definitions:
        grouped.setdefault(error.status_code, {})[error.detail] = error
    responses = {}
    for status, group in grouped.items():
        response = {
            'model': BuildError,
            'description': ', '.join(group),
            'content': {'application/json': {'examples': {
                code: {'value': {'detail': code}} for code in group
            }}},
        }
        if status == 401:
            response['headers'] = {'WWW-Authenticate': {
                'description': 'Bearer authentication challenge',
                'schema': {'type': 'string', 'const': 'Bearer'},
            }}
        if 'BUILD_COMMENT_RATE_LIMITED' in group:
            response['headers'] = {'Retry-After': {
                'description': 'Seconds before retrying comment creation',
                'schema': {'type': 'string', 'pattern': '^[0-9]+$'},
                'example': '60',
            }}
        responses[status] = response
    return responses


# FastAPI merges this anonymous alternative with the generated OAuth2 requirement.
# OpenAPI security alternatives are OR: either a bearer token or no credentials.
OPTIONAL_AUTH = {'security': [{}]}
