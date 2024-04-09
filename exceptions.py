import json
from fastapi import Response
from constants import HTTPErrorCode


class ErrorResponse:
    """
    API Error 응답 객체
    """
    default_obj = {}

    @classmethod
    def return_error(cls, enum: HTTPErrorCode):
        """
        에러가 발생해도 200으로 보내서 응답은 받게 함
        """
        message = cls.default_obj.copy()
        message['status_code'] = enum.value
        message['body'] = enum.name
        content = json.dumps(message)

        return Response(content=content, status_code=200, media_type="application/json")
