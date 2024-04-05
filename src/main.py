from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
)
from exceptions import ErrorResponse
from constants import HTTPErrorCode

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
    return ErrorResponse.return_error(HTTPErrorCode.BAD_REQUEST)
    # return {"message": "hi"}


@app.get("/home")
def home():
    return {"message": "home"}


@app.get("/home/{name}")
def home(name: str):
    return {"message": name}