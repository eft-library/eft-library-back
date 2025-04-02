import requests
import os
from dotenv import load_dotenv


load_dotenv()


class UserUtil:
    @staticmethod
    def verify_google_token(access_token: str):
        """
        구글 검증
        """
        response = requests.get(
            f"{os.getenv('GOOGLE_TOKEN_INFO_URL')}?access_token={access_token}"
        )

        if response.status_code != 200:
            return False
        data = response.json()
        return data["email"]
