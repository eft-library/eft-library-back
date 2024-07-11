import requests
from fastapi import FastAPI, HTTPException


NAVER_USER_INFO_URL = "https://openapi.naver.com/v1/nid/me"
GOOGLE_TOKEN_INFO_URL = "https://www.googleapis.com/oauth2/v1/tokeninfo"


class UserUtil:

    @staticmethod
    def verify_token(provider: str, access_token: str):
        """
        1차 토큰 분류
        """
        if provider == "naver":
            res = UserUtil.verify_naver_token(access_token)
            if res:
                return res
            else:
                return False
        else:
            res = UserUtil.verify_google_token(access_token)
            if res:
                return res
            else:
                return False

    @staticmethod
    def verify_naver_token(access_token: str):
        """
        naver 검증
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        response = requests.get(NAVER_USER_INFO_URL, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Naver access token")
        data = response.json()
        return data["response"]["email"]

    @staticmethod
    def verify_google_token(access_token: str):
        """
        구글 검증
        """
        response = requests.get(f"{GOOGLE_TOKEN_INFO_URL}?access_token={access_token}")

        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Google access token")
        data = response.json()
        return data["email"]
