import os
from dotenv import load_dotenv
import subprocess
# from kafka import KafkaProducerService
#
# kafka_producer_service = KafkaProducerService()
load_dotenv()


class ServerService:
    @staticmethod
    def rebuild_front():
        subprocess.Popen([os.getenv("BUILD_PATH")], shell=True)
        return True

    # @staticmethod
    # async def save_footprint():
    #     try:
    #         await kafka_producer_service.send_message("asd")
    #         return True
    #     except Exception as e:
    #         print(f"An error occurred: {e}")
    #         return False

