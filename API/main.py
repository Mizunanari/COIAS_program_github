from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import API.config as config
from API.routers import files, processes, ws, tests
from API.internal import admin


COIAS_DES = 'coiasフロントアプリからアクセスされるAPIです。\
    \n\n<img src="/static/icon.png" alt="drawing" width="200"/>'

tags_metadata = [
    {"name": "processes", "description": "backendで実行されるコマンドAPIです。"},
    {"name": "files", "description": "backendに送信するファイルの操作APIです。"},
    {"name": "tests", "description": "テスト用のAPIです。"},
]
app = FastAPI(
    title="COIAS API",
    description=COIAS_DES,
    version="0.3.1",
    openapi_tags=tags_metadata,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=config.WEB_ORIGINS,
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
app.include_router(admin.router)


# ディレクトリがなければつくる
config.FILES_PATH.mkdir(exist_ok=True)
