from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import API.config as config
from API.routers import files, processes, ws, tests


COIAS_DES = 'coiasフロントアプリからアクセスされるAPIです。\
    \n\n<img src="/static/icon.png" alt="drawing" width="200"/>'

tags_metadata = [
    {"name": "processes", "description": "backendで実行されるコマンドAPIです。"},
    {"name": "files", "description": "backendに送信するファイルの操作APIです。"},
    {"name": "test", "description": "テスト用のAPIです。"},
]
app = FastAPI(
    title="COIAS API",
    description=COIAS_DES,
    version="0.3.1",
    openapi_tags=tags_metadata,
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# https://fastapi.tiangolo.com/ja/tutorial/static-files/
app.mount("/static", StaticFiles(directory=config.DOC_IMAGE_PATH), name="icon")


app.include_router(files.router)
app.include_router(processes.router)
app.include_router(ws.router)
app.include_router(tests.router)


# ディレクトリがなければつくる
config.FILES_PATH.mkdir(exist_ok=True)
