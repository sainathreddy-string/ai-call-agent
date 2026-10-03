from fastapi import FastAPI

from app.config.settings import APP_NAME
from app.routes.webhook import router as webhook_router


app = FastAPI(title=APP_NAME)

app.include_router(webhook_router)


@app.get("/")
def home():
    return {
        "message": f"{APP_NAME} is running!"
    }