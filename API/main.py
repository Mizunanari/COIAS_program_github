import os
import subprocess
import shutil
import pathlib
import json
from datetime import datetime
import traceback
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from astropy.io import fits
import asyncio
from PIL import Image


COIAS_DES = 'coiasフロントアプリからアクセスされるAPIです。\
    \n\n<img src="/static/icon.png" alt="drawing" width="200"/>'

tags_metadata = [
    {"name": "command", "description": "backendで実行されるコマンドAPIです。"},
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
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPT_PATH = pathlib.Path("/opt")
PROGRAM_PATH = OPT_PATH / "coias-back-app"
IMAGES_PATH = OPT_PATH / "tmp_images"
FILES_PATH = OPT_PATH / "tmp_files"
SUBARU_PATH = PROGRAM_PATH / "SubaruHSC"
DOC_IMAGE_PATH = PROGRAM_PATH / "docs/image"

# https://fastapi.tiangolo.com/ja/tutorial/static-files/
app.mount("/static", StaticFiles(directory=DOC_IMAGE_PATH), name="icon")

# ディレクトリがなければつくる
FILES_PATH.mkdir(exist_ok=True)


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


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
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
                await manager.send_personal_message({'query': contents[0], 'progress': progress}, websocket)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(e, e.args)


@app.get("/", summary="ファイルアップロード確認用", tags=["test"])
async def main():
    """
    [localhost](http://localhost:8000/)
    """
    content = """
<body>
<form action="/uploadfiles/" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)


@app.get("/unknown_disp", summary="unknown_disp.txtを配列で取得", tags=["files"])
def get_unknown_disp(pj: int = -1):
    disp_path = pj_path(pj) / "unknown_disp.txt"

    if not disp_path.is_file():
        raise HTTPException(status_code=404)

    with disp_path.open() as f:
        result = f.read()

    result = split_list(result.split(), 4)

    return {"result": result}


@app.get("/log", summary="log.txtを配列で取得", tags=["files"])
def get_log(pj: int = -1):
    log_path = pj_path(pj) / "log.txt"

    if not log_path.is_file():
        raise HTTPException(status_code=404)

    with log_path.open() as f:
        result = f.read()

    if result == "":
        raise HTTPException(status_code=404)

    return {"result": result.split("\n")}


@app.get("/karifugo_disp", summary="karifugo_disp.txtを配列で取得", tags=["files"])
def get_karifugo_disp(pj: int = -1):
    disp_path = pj_path(pj) / "karifugo_disp.txt"

    if not disp_path.is_file():
        raise HTTPException(status_code=404)

    with disp_path.open() as f:
        result = f.read()

    result = split_list(result.split(), 4)

    return {"result": result}


@app.get("/numbered_disp", summary="numbered_disp.txtを配列で取得", tags=["files"])
def get_numbered_disp(pj: int = -1):
    disp_path = pj_path(pj) / "numbered_disp.txt"

    if not disp_path.is_file():
        raise HTTPException(status_code=404)

    with disp_path.open() as f:
        result = f.read()

    result = split_list(result.split(), 4)

    return {"result": result}


@app.get("/fits_size", summary="fitsファイルのサイズを取得", tags=["files"])
def get_FITS_SIZE(pj: int = -1):
    fits_path = pj_path(pj) / "warp01_bin.fits"

    if not fits_path.is_file():
        raise HTTPException(status_code=404)

    FITSSIZES = (
        fits.open(fits_path)[0].header["NAXIS1"],
        fits.open(fits_path)[0].header["NAXIS2"],
    )

    return {"result": FITSSIZES}


@app.post("/uploadfiles/", summary="fileアップロード", tags=["files"])
async def create_upload_files(files: list[UploadFile]):
    """
    複数のファイルをアップロードする場合はこちらのページを使用すると良い

    [localhost:8000](http://localhost:8000/)

    __参考__
    - [Request Files - FastAPI](https://fastapi.tiangolo.com/tutorial/request-files/#uploadfile)
    - [フォーム - React](https://ja.reactjs.org/docs/forms.html)
    """  # noqa:E501

    dt = str(datetime.now())
    log = {
        "file_list": [],
        "create_time": [],
        "zip_upload": [],
    }
    log_path = FILES_PATH / "log"

    # logファイルがあれば読み込み
    if log_path.is_file():

        with log_path.open(mode="r") as conf:
            conf_json = conf.read()

        if not conf_json == "":
            log = json.loads(conf_json)

    # projectに割り振られる番号を生成
    if log["file_list"]:
        last_project = log["file_list"][-1] + 1
    else:
        last_project = 1

    # logを更新
    log["file_list"].append(last_project)
    log["create_time"].append(dt)
    log["zip_upload"].append(False)

    # logを書き込み
    json_str = json.dumps(log)
    with log_path.open(mode="w") as conf:
        conf.write(json_str)

    # プロジェクトディレクトリを作成
    file_name = str(log["file_list"][-1])
    current_project_folder_path = FILES_PATH / file_name
    current_project_folder_path.mkdir()

    # fileを保存
    for file in files:
        tmp_path = current_project_folder_path / file.filename

        try:
            with tmp_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        finally:
            file.file.close()

    # プロジェクトディレクトリの内容を取得
    files_dir = [fd.name for fd in FILES_PATH.iterdir() if fd.is_dir()]
    project_files = [pf.name for pf in current_project_folder_path.iterdir()]

    files_dir.sort(key=int)
    project_files.sort()

    return {"tmp_files_projects": files_dir, "project_files": project_files, "log": log}


@app.get("/project-list", summary="projectのリストを返却します", tags=["files"], status_code=200)
def run_get_project_list():
    # fmt:off
    """
    projectのリストを返却します。  
    projectはファイルがアップロードされるたびに、作成されます。

    __res__

    ```
    {
        "tmp_files_projects": [
            "1",
            "2"
        ],
        "log": {
            "file_list": [
                1,
                2
            ],
            "create_time": [
                "2022-03-25 07:33:34.558611",
                "2022-03-25 08:03:34.850662"
            ],
            "zip_upload": [
                false,
                false
            ]
        }
    }
    ```

    tmp_files_projects  
    実際にtmpフォルダーに配置されている、プロジェクトフォルダー。

    log  
    project作成時に更新される、プロジェクトの詳細情報。

    """  # noqa
    # fmt:on
    log_path = FILES_PATH / "log"

    # logファイルがあれば読み込み
    if log_path.is_file():

        with log_path.open(mode="r") as conf:
            conf_json = conf.read()

        if not conf_json == "":
            log = json.loads(conf_json)

    else:
        raise HTTPException(status_code=404)

    # プロジェクトディレクトリpathを作成
    file_name = str(log["file_list"][-1])
    current_project_folder_path = FILES_PATH / file_name

    # プロジェクトディレクトリの内容を取得
    files_dir = [fd.name for fd in FILES_PATH.iterdir() if fd.is_dir()]
    project_files = [pf.name for pf in current_project_folder_path.iterdir()]

    files_dir.sort(key=int)
    project_files.sort()

    return {"tmp_files_projects": files_dir, "log": log}


@app.get("/project", summary="projectのフォルダ内容を返却します", tags=["files"])
def run_get_project(pj: int = -1):
    # fmt:off
    """
    projectのフォルダ内容を返却します。  

    __res__

    ```
    {
        "project_files": [
            "1_disp-coias.png",
            "1_disp-coias_nonmask.png",
            "2_disp-coias.png",
            "2_disp-coias_nonmask.png",
                    ・
                    ・
                    ・
        ]
    }
    ```


    """  # noqa
    # fmt:on

    log_path = FILES_PATH / "log"

    # logファイルがあれば読み込み
    if log_path.is_file():

        with log_path.open(mode="r") as conf:
            conf_json = conf.read()

        if not conf_json == "":
            log = json.loads(conf_json)

    else:
        raise HTTPException(status_code=404)

    # プロジェクトディレクトリを作成
    file_name = str(log["file_list"][-1])
    current_project_folder_path = FILES_PATH / file_name

    # プロジェクトディレクトリの内容を取得
    project_files = [pf.name for pf in current_project_folder_path.iterdir()]
    project_files.sort()

    return {"project_files": project_files}


@app.delete("/deletefiles", summary="tmp_imageの中身を削除", tags=["files"], status_code=200)
def run_deletefiles():

    for f in IMAGES_PATH.glob("*.png"):
        if f.is_file:
            f.unlink()


@app.put("/copy", summary="プロジェクトから「tmp_image」へpng画像コピー", tags=["files"])
def run_copy(pj: int = -1):
    # fmt: off
    """
    「tmp_image」にあるpng画像はnginxによって配信されます。  
    配信されているpng画像のリストを配列で返却します。

    __res__

    ```JSON
    {
        "result": [
            "1_disp-coias.png",
            "1_disp-coias_nonmask.png",
            "2_disp-coias.png",
            "2_disp-coias_nonmask.png",
            "3_disp-coias.png",
            "3_disp-coias_nonmask.png",
            "4_disp-coias.png",
            "4_disp-coias_nonmask.png",
            "5_disp-coias.png",
            "5_disp-coias_nonmask.png",
        ]
    }
    ```
    """ # noqa
    # fmt: on
    for f in pj_path(pj).glob("*.png"):
        if f.is_file():
            shutil.copy(f, IMAGES_PATH)

    file_list = []
    for i in IMAGES_PATH.glob("*.png"):
        file_list.append(i.name)
    file_list.sort()

    return {"result": file_list}


@app.put("/memo", summary="outputを出力", tags=["files"])
def run_memo(output_list: list, pj: int = -1):
    # fmt: off
    """
    bodyの配列からmemo.txtを出力します。

    __body__

    ```JSON
    [
        "000001",
        "000010",
        "000013",
        "000012",
        "000005",
        "000003",
        "000004",
        "000009",
        "000000",
        "000006",
        "000014"
    ]
    ```
    """ # noqa
    # fmt: on

    memo = ""
    result = ""
    memo_path = pj_path(pj) / "memo.txt"

    for i, list in enumerate(output_list):
        memo = memo + str(list)
        if not i == (len(output_list) - 1):
            memo = memo + "\n"

    with memo_path.open(mode="w") as f:
        f.write(memo)

    with memo_path.open(mode="r") as f:
        result = f.read()

    return {"memo.txt": result}


@app.get("/memo", summary="memoを取得", tags=["files"])
def get_memo(pj: int = -1):
    # fmt: off
    """
    memo.txtを出力します。

    __body__

    ```JSON
    [
        "000001",
        "000010",
        "000013",
        "000012",
        "000005",
        "000003",
        "000004",
        "000009",
        "000000",
        "000006",
        "000014"
    ]
    ```
    """ # noqa
    # fmt: on

    memo_path = pj_path(pj) / "memo.txt"

    if not memo_path.is_file():
        raise HTTPException(status_code=404)

    with memo_path.open() as f:
        result = f.read()

    if result == "":
        raise HTTPException(status_code=404)

    return {"memo": result.split("\n")}


@app.get("/memo_manual", summary="memo_manualを取得", tags=["files"])
def get_memomanual(pj: int = -1):
    # fmt: off
    """
    memo_manual.txtを出力します。

    __body__

    ```JSON
    [
        "000001",
        "000010",
        "000013",
        "000012",
        "000005",
        "000003",
        "000004",
        "000009",
        "000000",
        "000006",
        "000014"
    ]
    ```
    """ # noqa
    # fmt: on

    memo_path = pj_path(pj) / "memo_manual.txt"

    if not memo_path.is_file():
        raise HTTPException(status_code=404)

    with memo_path.open() as f:
        result = f.read()

    if result == "":
        raise HTTPException(status_code=404)

    memo_manual = []
    for line in result.split("\n"):
        splitedLine = line.split(" ")
        result = (
            splitedLine[0]
            + " "
            + splitedLine[1]
            + " "
            + convertFits2PngCoords([int(splitedLine[2]), int(splitedLine[3])])
            + " "
            + convertFits2PngCoords([int(splitedLine[4]), int(splitedLine[5])])
            + " "
            + convertFits2PngCoords([int(splitedLine[6]), int(splitedLine[7])])
            + " "
            + convertFits2PngCoords([int(splitedLine[8]), int(splitedLine[9])])
        )
        memo_manual.append(result)

    return {"memo_manual": memo_manual}


@app.put("/memo_manual", summary="手動測定の出力", tags=["command"])
def run_memo_manual(output_list: list, pj: int = -1):
    """
    memo_manual.txtへ出力
    """

    # fmt: off
    """
    bodyの配列からmemo_manual.txtを出力します。

    __body__

    ```JSON
    [
        "000001",
        "000010",
        "000013",
        "000012",
        "000005",
        "000003",
        "000004",
        "000009",
        "000000",
        "000006",
        "000014"
    ]
    ```
    """ # noqa
    # fmt: on

    memo_manual = ""
    result = ""
    memo_manual_path = pj_path(pj) / "memo_manual.txt"

    for list in output_list:
        for list_obj in list:
            translated_line = (
                str(list_obj["name"])
                + " "
                + str(list_obj["page"])
                + " "
                + convertPng2FitsCoords(
                    [int(list_obj["center"]["x"]), int(list_obj["center"]["y"])]
                )
                + " "
                + convertPng2FitsCoords(
                    [int(list_obj["actualA"]["x"]), int(list_obj["actualA"]["y"])]
                )
                + " "
                + convertPng2FitsCoords(
                    [int(list_obj["actualB"]["x"]), int(list_obj["actualB"]["y"])]
                )
                + " "
                + convertPng2FitsCoords(
                    [int(list_obj["actualC"]["x"]), int(list_obj["actualC"]["y"])]
                )
            )
            memo_manual = memo_manual + str(translated_line)
            if not (
                list_obj["name"] == output_list[-1][-1]["name"]
                and list_obj["page"] == output_list[-1][-1]["page"]
            ):
                memo_manual = memo_manual + "\n"

    with memo_manual_path.open(mode="w") as f:
        f.write(memo_manual)

    with memo_manual_path.open(mode="r") as f:
        result = f.read()

    return {"memo_manual.txt": result}


@app.put(
    "/manual_name_modify_list",
    summary="manual_name_modify_list.txtを書き込み",
    tags=["files"],
)
def write_modify_list(modifiedList: list, pj: int = -1):
    # fmt: off
    """
    textの配列を、manual_name_modify_list.txtに書き込みます。
    """ # noqa
    # fmt: on

    text = ""
    for (i, oldNewPair) in enumerate(modifiedList):
        text = text + "{} {}".format(oldNewPair[0], oldNewPair[1])
        if not i == len(modifiedList) - 1:
            text = text + "\n"
    text_path = pj_path(pj) / "manual_name_modify_list.txt"

    with text_path.open(mode="w") as f:
        f.write(text)


@app.put("/preprocess", summary="最新のMPCデータを取得", tags=["command"], status_code=200)
def run_preprocess(pj: int = -1):

    os.chdir(pj_path(pj).as_posix())
    result = subprocess.run(["preprocess"])
    errorHandling(result.returncode)


@app.put("/startsearch2R", summary="ビニング&マスク", tags=["command"], status_code=200)
def run_startsearch2R(binning: int = 2, pj: int = -1, sn: int = 2000):

    if binning != 2 and binning != 4:
        raise HTTPException(status_code=400)
    else:
        binning = str(binning)

    os.chdir(pj_path(pj).as_posix())
    result = subprocess.run(
        ["startsearch2R", "sn={}".format(sn)], input=binning, encoding="UTF-8"
    )
    errorHandling(result.returncode)


@app.put(
    "/prempsearchC-before", summary="精密軌道取得 前処理", tags=["command"], status_code=200
)
def run_prempsearchC_before(pj: int = -1):

    os.chdir(pj_path(pj).as_posix())
    result = subprocess.run(["prempsearchC-before"], shell=True)
    errorHandling(result.returncode)


@app.put("/prempsearchC-after", summary="精密軌道取得 後処理", tags=["command"], status_code=200)
def run_prempsearchC_after(pj: int = -1):

    os.chdir(pj_path(pj).as_posix())
    result = subprocess.run(["prempsearchC-after"], shell=True)
    errorHandling(result.returncode)


@app.put("/astsearch_new", summary="自動検出", tags=["command"], status_code=200)
def run_astsearch_new(pj: int = -1, nd: int = 4, ar: int = 6):

    os.chdir(pj_path(pj).as_posix())
    cmdStr = "astsearch_new nd={} ar={}".format(nd, ar)
    print(cmdStr)
    result = subprocess.run(cmdStr, shell=True)
    errorHandling(result.returncode)


@app.put(
    "/getMPCORB_and_mpc2edb", summary="出力ファイル整形", tags=["command"], status_code=200
)
def run_getMPCORB_and_mpc2edb(pj: int = -1):

    os.chdir(pj_path(pj).as_posix())
    result = subprocess.run(["getMPCORB_and_mpc2edb_for_button"])
    errorHandling(result.returncode)


@app.put("/redisp", summary="再描画による確認作業", tags=["command"])
def run_redisp(pj: int = -1):
    """
    redispが動作し、redisp.txtを配列で取得

    __res__

    ```JSON
    {
        "result": [
            [
                "w7794",
                "3",
                "1965.52",
                "424.56"
            ],
            [
                "w7794",
                "2",
                "1927.21",
                "416.32"
            ]
        ]
    }
    ```

    """  # noqa

    redisp_path = pj_path(pj) / "redisp.txt"

    if not redisp_path.is_file():
        raise HTTPException(status_code=404)

    with redisp_path.open() as f:
        result = f.read()

    result = split_list(result.split(), 4)

    return {"result": result}


@app.put(
    "/AstsearchR_between_COIAS_and_ReCOIAS",
    summary="探索モード後に走り自動検出天体の番号の付け替えを行う",
    tags=["command"],
)
def run_AstsearchR_between_COIAS_and_ReCOIAS(num: int, pj: int = -1):

    os.chdir(pj_path(pj).as_posix())
    resultError = subprocess.run(["AstsearchR_between_COIAS_and_ReCOIAS", str(num)])
    errorHandling(resultError.returncode)
    redisp_path = pj_path(pj) / "redisp.txt"

    if not redisp_path.is_file():
        raise HTTPException(status_code=404)

    with redisp_path.open() as f:
        result = f.read()

    result = split_list(result.split(), 4)

    return result


@app.put(
    "/AstsearchR_afterReCOIAS", summary="レポートモードに入ったとき発火し、send_mpcを作成", tags=["command"]
)
def run_Astsearch_afterReCOIAS(pj: int = -1):

    os.chdir(pj_path(pj).as_posix())
    resultError = subprocess.run(["AstsearchR_afterReCOIAS"])
    errorHandling(resultError.returncode)

    send_path = pj_path(pj) / "send_mpc.txt"
    result = ""

    with send_path.open(mode="r") as f:
        result = f.read()

    if not send_path.is_file():
        raise HTTPException(status_code=404)

    return {"send_mpc": result}

@app.put("/get_mpc", summary="2回目以降にレポートモードに入ったときにsend_mpcを取得するだけのAPI", tags=["command"])
def get_mpc(pj: int = -1):
    send_path = pj_path(pj) / "send_mpc.txt"
    result = ""

    with send_path.open(mode="r") as f:
        result = f.read()

    if not send_path.is_file():
        raise HTTPException(status_code=404)

    return {"send_mpc": result}

@app.put("/AstsearchR_after_manual", summary="手動測定：再描画による確認作業", tags=["command"])
def run_AstsearchR_after_manual(pj: int = -1):

    os.chdir(pj_path(pj).as_posix())
    resultError = subprocess.run(["AstsearchR_after_manual"])
    errorHandling(resultError.returncode)

    send_path = pj_path(pj) / "reredisp.txt"
    result = ""

    with send_path.open(mode="r") as f:
        result = f.read()

    if not send_path.is_file():
        raise HTTPException(status_code=404)

    return {"reredisp": result}


@app.get("/final_disp", summary="最終確認モードで表示させる天体一覧を記したfinal_disp.txtを取得する", tags=["command"])
def get_finaldisp(pj: int = -1):
    final_disp_path = pj_path(pj) / "final_disp.txt"

    if not final_disp_path.is_file():
        raise HTTPException(status_code=404)

    with final_disp_path.open() as f:
        result = f.read()

    result = split_list(result.split(), 4)

    return {"result": result}



@app.get("/final_all", summary="final_allを取得", tags=["files"])
def get_finalall(pj: int = -1):

    final_all_path = pj_path(pj) / "final_all.txt"

    if not final_all_path.is_file():
        raise HTTPException(status_code=404)

    with final_all_path.open() as f:
        result = f.read()

    if result == "":
        raise HTTPException(status_code=404)

    return {"finalall": result}


@app.get("/progress", summary="progress.txtに記載の進捗率などの情報を取得", tags=["files"])
def get_progress(pj: int = -1):
    progress_path = pj_path(pj) / "progress.txt"

    try:
        f = open(progress_path, "r")
        line = f.readline()
        f.close()

        contents = line.split()
        query = contents[0]
        progress = str(int((int(contents[1]) / int(contents[2])) * 100.0)) + "%"

        result = {"query": query, "progress": progress}
    except FileNotFoundError:
        result = {"query": "initial", "progress": "0%"}
    except Exception:
        result = {"query": "N/A", "progress": "N/A"}
    finally:
        return {"result": result}


@app.get("/time_list", summary="画像の時刻リストが記載されたformatted_time_list.txtの内容を配列で取得", tags=["files"])
def get_time_list(pj: int = -1):
    time_list_path = pj_path(pj) / "formatted_time_list.txt"

    if not time_list_path.is_file():
        raise HTTPException(status_code=404)

    with time_list_path.open() as f:
        result = f.readlines()

    for i in range(len(result)):
        result[i] = result[i].rstrip("\n")

    return {"result": result}


@app.get("/predicted_disp", summary="直近の測定データから予測された天体の位置を記載したpredicted_disp.txtを取得する", tags=["command"])
def get_predicted_disp(pj: int = -1):
    predicted_disp_path = pj_path(pj) / "predicted_disp.txt"

    if not predicted_disp_path.is_file():
        raise HTTPException(status_code=404)

    with predicted_disp_path.open() as f:
        result = f.read()

    result = split_list(result.split(), 5)

    return {"result": result}


def split_list(list, n):
    """
    リストをサブリストに分割する
    :param l: リスト
    :param n: サブリストの要素数
    :return:
    """
    for idx in range(0, len(list), n):
        yield list[idx : idx + n]


def pj_path(pj, is_websocket=False):

    log_path = FILES_PATH / "log"

    path = ""

    if log_path.is_file():
        with log_path.open(mode="r") as conf:
            conf_json = conf.read()

        if not conf_json == "":
            log = json.loads(conf_json)
        else:
            return

        file_name = log["file_list"][pj]
        path = FILES_PATH / str(file_name)
    elif is_websocket:
        path = FILES_PATH / ""
    else:
        raise HTTPException(
            404, detail={"place": "tmp_files", "reason": "log fileがありません"}
        )

    return path


def errorHandling(errorNumber: int):
    errorList = {"place": "正常終了", "reason": "正常終了"}

    if errorNumber != 0:

        numString = str(errorNumber)

        if numString[-2] == "1":
            errorList.update({"place": "事前処理"})
        elif numString[-2] == "2":
            errorList.update({"place": "ビニングマスク"})
        elif numString[-2] == "3":
            errorList.update({"place": "軌道取得（確定番号）"})
        elif numString[-2] == "4":
            errorList.update({"place": "軌道取得（仮符号）"})
        elif numString[-2] == "5":
            errorList.update({"place": "自動検出"})
        elif numString[-2] == "6":
            errorList.update({"place": "探索モード後処理"})
        elif numString[-2] == "7":
            errorList.update({"place": "レポートモード前処理"})
        elif numString[-2] == "8":
            errorList.update({"place": "手動測定後処理"})
        else:
            return errorList

        if numString[-1] == "1":
            errorList.update({"reason": "5枚のwrap画像をアップロードしてから解析をして下さい。"})
        elif numString[-1] == "2":
            errorList.update({"reason": "インターネットに接続してから解析をして下さい。"})
        elif numString[-1] == "3":
            errorList.update({"reason": "軌道取得を数回やり直して下さい。"})
        elif numString[-1] == "4":
            errorList.update(
                {
                    "reason": "必要な中間ファイルがありません。全自動処理を中止し、いくつか前の適切な処理からやり直して下さい。数回やり直してもエラーが出る場合、開発者にlog.txtをメールで送信して下さい。Downloadsボタンからlog.txtをダウンロードできます。"
                }
            )
        elif numString[-1] == "5":
            errorList.update(
                {
                    "reason": "予期せぬエラーが発生しました。数回やり直してもエラーが出る場合、開発者にlog.txtをメールで送信して下さい。Downloadsボタンからlog.txtをダウンロードできます。"
                }
            )
        else:
            return errorList

        raise HTTPException(status_code=400, detail=errorList)

    return errorList


# Functions for converting fits coords between png and fits #
def convertFits2PngCoords(fitsPosition):
    try:
        images_pj_path = pj_path(-1)
        PNGSIZES = Image.open(images_pj_path / "01_disp-coias.png").size
        FITSSIZES = (
            fits.open(images_pj_path / "warp01_bin.fits")[0].header["NAXIS1"],
            fits.open(images_pj_path / "warp01_bin.fits")[0].header["NAXIS2"],
        )
        if fitsPosition[0] > FITSSIZES[0] or fitsPosition[1] > FITSSIZES[1]:
            raise ValueError(
                "invalid fits positions! X={0:d} Xmax={1:d} Y={2:d} Ymax={3:d}".format(
                    fitsPosition[0], FITSSIZES[0], fitsPosition[1], FITSSIZES[1]
                )
            )
        fitsXRelPos = float(fitsPosition[0]) / float(FITSSIZES[0])
        fitsYRelPos = float(fitsPosition[1]) / float(FITSSIZES[1])

        pngXRelPos = fitsXRelPos
        pngYRelPos = 1.0 - fitsYRelPos

        pngXPosition = int(pngXRelPos * PNGSIZES[0])
        pngYPosition = int(pngYRelPos * PNGSIZES[1])
        return str(pngXPosition) + " " + str(pngYPosition)
    except FileNotFoundError:
        print("1st png file or fits file are not found!")
        print(traceback.format_exc())


def convertPng2FitsCoords(pngPosition):
    try:
        images_pj_path = pj_path(-1)
        PNGSIZES = Image.open(images_pj_path / "01_disp-coias.png").size
        FITSSIZES = (
            fits.open(images_pj_path / "warp01_bin.fits")[0].header["NAXIS1"],
            fits.open(images_pj_path / "warp01_bin.fits")[0].header["NAXIS2"],
        )
        if pngPosition[0] > PNGSIZES[0] or pngPosition[1] > PNGSIZES[1]:
            raise ValueError(
                "invalid png positions! X={0:d} Xmax={1:d} Y={2:d} Ymax={3:d}".format(
                    pngPosition[0], PNGSIZES[0], pngPosition[1], PNGSIZES[1]
                )
            )

        pngXRelPos = float(pngPosition[0]) / float(PNGSIZES[0])
        pngYRelPos = float(pngPosition[1]) / float(PNGSIZES[1])

        fitsXRelPos = pngXRelPos
        fitsYRelPos = 1.0 - pngYRelPos

        fitsXPosition = int(fitsXRelPos * FITSSIZES[0])
        fitsYPosition = int(fitsYRelPos * FITSSIZES[1])
        return str(fitsXPosition) + " " + str(fitsYPosition)
    except FileNotFoundError:
        print("1st png file or fits file are not found!")
        print(traceback.format_exc())


######################################################################
