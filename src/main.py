from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "hi"}

@app.get("/home")
def home():
    return {"message": "home"}

@app.get("/home/{name}")
def home(name: str):
    return {"message": name}