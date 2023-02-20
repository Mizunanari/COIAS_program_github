import os
import json
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import print_progress
from API.utils import pj_path


router = APIRouter(
    prefix="/ws",
    tags=["ws"],
    responses={404: {"description": "Not found"}},
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: json, websocket: WebSocket):
        await websocket.send_json(message)


manager = ConnectionManager()


@router.websocket("/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    os.chdir(pj_path(-1, True).as_posix())
    await manager.connect(websocket)
    # TODO : fileがまだ作られていない時、接続してやめてが繰り返される
    try:
        while True:
            progress_path = pj_path(-1, True) / "progress.txt"
            if progress_path.is_file():
                f = open(progress_path, "r")
                line = f.readline()
                f.close()

                contents = line.split()
                progress = str(int((int(contents[1]) / int(contents[2])) * 100.0)) + "%"

                # await manager.send_personal_message(f"You wrote: {data}", websocket)
                await manager.send_personal_message(
                    {"query": contents[0], "progress": progress}, websocket
                )

                if progress == "100%":
                    print_progress.print_progress(
                        nTotalCheckPoints=1,
                        currentCheckPoint=0,
                        currentButtonName="ProcessDone",
                    )
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(e, e.args)

