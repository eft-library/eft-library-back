from fastapi import APIRouter, File, UploadFile
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.board.service import BoardService
from dotenv import load_dotenv
import os

load_dotenv()


router = APIRouter(tags=["Board"])


@router.post("/upload_image")
def upload_image(file: UploadFile = File(...)):
    file_location, unique_filename = BoardService.save_file(file, file.filename)
    # 로직 변경 -> scp로 파일 전달에서 바로 저장공간을 연동으로 변경
    # if BoardService.upload_to_remote(file_location, unique_filename):
    image_url = (
        f"{os.getenv('NAS_DATA')}{os.getenv('BOARD_IMAGE_PATH')}/{unique_filename}"
    )
    return CustomResponse.response(image_url, HTTPCode.OK, Message.SUCCESS)
