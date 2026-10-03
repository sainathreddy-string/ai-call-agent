from fastapi import APIRouter

router = APIRouter()


@router.get("/webhook/test")
def webhook_test():
    return {
        "message": "Webhook is working!"
    }