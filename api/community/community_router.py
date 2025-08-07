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
from PIL import Image  # ✅ 추가

load_dotenv()

router = APIRouter(tags=["Community"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

minio_client = Minio(
    os.getenv("MINIO_ENDPOINT").replace("http://", "").replace("https://", ""),
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=False,
)

bucket_name = "eftlibrary"
folder_name = "tkl_community/posts_image"


@router.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    filename_wo_ext = os.path.splitext(file.filename.replace(" ", "_"))[0]
    object_name = (
        f"{folder_name}/{timestamp}_{filename_wo_ext}.webp"  # ✅ .webp 확장자로 저장
    )

    try:
        # 1. 이미지 열기 (UploadFile -> PIL Image)
        image = Image.open(file.file)

        # 2. 리사이징 (선택적): 너무 큰 이미지 줄이기
        max_size = (1200, 1200)
        image.thumbnail(max_size)

        # 3. WebP로 저장
        buffer = io.BytesIO()
        image.save(buffer, format="WEBP", quality=80, method=6)  # ✅ 압축률 조정
        buffer.seek(0)

        # 4. MinIO에 업로드
        minio_client.put_object(
            bucket_name,
            object_name,
            data=buffer,
            length=buffer.getbuffer().nbytes,
            content_type="image/webp",
        )

    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"MinIO 업로드 실패: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 처리 실패: {e}")

    # 공개 접근 가능한 URL 생성
    url = f"https://image.eftlibrary.com/{bucket_name}/{object_name}"

    result = {"image_url": url}

    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
