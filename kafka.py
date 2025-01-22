# kafka_producer_service.py
# from aiokafka import AIOKafkaProducer
# import os
# from dotenv import load_dotenv
#
# load_dotenv()
#
# KAFKA_BROKER = os.getenv("KAFKA_BROKER")
# KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
#
#
# class KafkaProducerService:
#     _instance = None
#     producer = None  # 클래스 변수로 producer 객체 생성
#
#     def __new__(cls, *args, **kwargs):
#         if cls._instance is None:
#             cls._instance = super(KafkaProducerService, cls).__new__(cls)
#         return cls._instance
#
#     async def start(self):
#         """Kafka Producer 초기화 및 시작"""
#         if not self.producer:
#             self.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKER)
#             await self.producer.start()
#
#     async def send_message(self, message: str):
#         """Kafka에 메시지 전송"""
#         if not self.producer:
#             raise Exception("Producer not started!")
#         await self.producer.send_and_wait(KAFKA_TOPIC, message.encode())
#
#     async def stop(self):
#         """Kafka Producer 종료"""
#         if self.producer:
#             await self.producer.stop()
#             self.producer = None  # 종료 후 producer 초기화
