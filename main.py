from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from api.router import api_router
from fastapi.openapi.docs import get_swagger_ui_html
from kafka import KafkaProducerService

load_dotenv()

app = FastAPI(title="eft-library-back")

kafka_producer_service = KafkaProducerService()


@app.get("/docs")
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",  # FastAPI 자동 생성된 OpenAPI 스키마 경로
        title="Swagger UI",
    )


@app.on_event("startup")
async def startup():
    await kafka_producer_service.start()
    print("Kafka Producer started.")


@app.on_event("shutdown")
async def shutdown():
    await kafka_producer_service.stop()
    print("Kafka Producer stopped.")

app.include_router(api_router, prefix=os.getenv("API_PREFIX"))

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
