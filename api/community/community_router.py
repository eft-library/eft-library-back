import io
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from api.response import CustomResponse
from fastapi.security import OAuth2PasswordBearer
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv
from util.constants import HTTPCode
from api.constants import Message
import os
from datetime import datetime

load_dotenv()

router = APIRouter(tags=["Roadmap"])

# JWT를 헤더에서 추출하는 의존성 함수
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

minio_client = Minio(
    os.getenv("MINIO_ENDPOINT"),  # MinIO 서버 주소
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=False,  # https 사용 시 True
)

bucket_name = "eftlibrary"
folder_name = "tkl_community/posts_image"


@router.post("/community/upload_image")
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    object_name = f"{folder_name}/{timestamp}_{file.filename.replace(' ', '_')}"

    try:
        # 업로드를 위해 파일 내용을 바이트로 읽기
        data = await file.read()
        # MinIO에 업로드
        minio_client.put_object(
            bucket_name,
            object_name,
            data=io.BytesIO(data),
            length=len(data),
            content_type=file.content_type,
        )
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"MinIO 업로드 실패: {e}")

    # 공개 접근 가능한 URL 생성 (MinIO 설정에 따라 다름)
    url = f"https://image.eftlibrary.com/{bucket_name}/{object_name}"

    result = {"image_url": url}
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
