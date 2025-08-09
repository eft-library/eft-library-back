from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from api.response import CustomResponse
from fastapi.security import OAuth2PasswordBearer
from api.user.util import UserUtil
from util.constants import HTTPCode
from api.constants import Message
from api.community.service import CommunityService
from api.community.community_req_models import CreateCommunity, UpdateCommunity, ViewCount, PostReaction


router = APIRouter(tags=["Community"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    result = CommunityService.upload_image(file)
    if result is None:
        raise HTTPException(status_code=500, detail=f"이미지 처리 실패")
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)

@router.post("/create_posts")
def create_posts(post_info: CreateCommunity, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityService.create_posts(post_info, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)
