import shutil
import os
import subprocess
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()


class BoardService:
    @staticmethod
    def save_file(file, filename):
        os.makedirs(os.getenv("LOCAL_UPLOAD_PATH"), exist_ok=True)
        file_extension = filename.split(".")[-1]
        unique_filename = f"{uuid4()}.{file_extension}"
        file_location = os.path.join(os.getenv("LOCAL_UPLOAD_PATH"), unique_filename)

        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return file_location, unique_filename

    @staticmethod
    def upload_to_remote(local_path: str, filename: str) -> bool:
        print([
                    "sshpass",
                    "-p",
                    os.getenv("SERVER_PW"),
                    "scp",
                    "-O",
                    "-P",
                    os.getenv("SERVER_PORT"),
                    local_path,
                    f"{os.getenv('SERVER_HOST')}:{os.getenv('SERVER_PATH')}/{filename}",
                ])
        try:
            subprocess.run(
                [
                    "sshpass",
                    "-p",
                    os.getenv("SERVER_PW"),
                    "scp",
                    "-O",
                    "-P",
                    os.getenv("SERVER_PORT"),
                    local_path,
                    f"{os.getenv('SERVER_HOST')}:{os.getenv('SERVER_PATH')}/{filename}",
                ],
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False
