from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
)
from api.router import api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title='tarkov-korea-wiki-back',
    openapi_url=f"/api/v1/openapi.json",
    docs_url=None,
    redoc_url=None)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


@app.get("/")
def root():
    return {"message": "hi"}


app.include_router(api_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, # cookie 포함 여부를 설정한다. 기본은 False
    allow_methods=["*"],    # 허용할 method를 설정할 수 있으며, 기본값은 'GET'이다.
    allow_headers=["*"],	# 허용할 http header 목록을 설정할 수 있으며 Content-Type, Accept, Accept-Language, Content-Language은 항상 허용된다.
)