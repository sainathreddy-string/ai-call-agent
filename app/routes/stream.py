from fastapi import APIRouter, WebSocket

router = APIRouter()


@router.websocket("/stream")
async def stream(websocket: WebSocket):
    await websocket.accept()

    await websocket.send_text("WebSocket connected")

    while True:
        message = await websocket.receive_text()
        print(f"Received: {message}")