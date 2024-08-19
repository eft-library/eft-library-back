import os
from dotenv import load_dotenv
import subprocess

load_dotenv()


class ServerService:
    @staticmethod
    def rebuild_front():
        subprocess.run([os.getenv("BUILD_PATH")], shell=True)

        return True
