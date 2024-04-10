
class CustomResponse:
    """
    API 응답 객체
    """
    @classmethod
    def response(cls, response, code, msg):
        return {
            "status": code,
            "msg": msg,
            "data": response
        }
