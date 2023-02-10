import shutil
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from astropy.io import fits
from API.utils import pj_path, split_list, convertFits2PngCoords
import API.config as config
from ..dependencies import get_token_header


router = APIRouter(
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/unknown_disp", summary="unknown_disp.txtを配列で取得", tags=["files"])
def get_unknown_disp(pj: int = -1):
    disp_path = pj_path(pj) / "unknown_disp.txt"

    if not disp_path.is_file():
        raise HTTPException(status_code=404)

    with disp_path.open() as f:
        result = f.read()

    result = split_list(result.split(), 4)

    return {"result": result}


@router.get("/log", summary="log.txtを配列で取得", tags=["files"])
def get_log(pj: int = -1):
    log_path = pj_path(pj) / "log.txt"

    if not log_path.is_file():
        raise HTTPException(status_code=404)

    with log_path.open() as f:
        result = f.read()

    if result == "":
        raise HTTPException(status_code=404)

    return {"result": result.split("\n")}


@router.get("/karifugo_disp", summary="karifugo_disp.txtを配列で取得", tags=["files"])
def get_karifugo_disp(pj: int = -1):
    disp_path = pj_path(pj) / "karifugo_disp.txt"

    if not disp_path.is_file():
        raise HTTPException(status_code=404)

    with disp_path.open() as f:
        result = f.read()

    result = split_list(result.split(), 4)

    return {"result": result}


@router.get("/numbered_disp", summary="numbered_disp.txtを配列で取得", tags=["files"])
def get_numbered_disp(pj: int = -1):
    disp_path = pj_path(pj) / "numbered_disp.txt"

    if not disp_path.is_file():
        raise HTTPException(status_code=404)

    with disp_path.open() as f:
        result = f.read()

    result = split_list(result.split(), 4)

    return {"result": result}


@router.get("/fits_size", summary="fitsファイルのサイズを取得", tags=["files"])
def get_FITS_SIZE(pj: int = -1):
    fits_path = pj_path(pj) / "warp01_bin.fits"

    if not fits_path.is_file():
        raise HTTPException(status_code=404)

    FITSSIZES = (
        fits.open(fits_path)[0].header["NAXIS1"],
        fits.open(fits_path)[0].header["NAXIS2"],
    )

    return {"result": FITSSIZES}


@router.post("/uploadfiles", summary="fileアップロード", tags=["files"])
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
    log_path = config.FILES_PATH / "log"

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
    log["file_list"].routerend(last_project)
    log["create_time"].routerend(dt)
    log["zip_upload"].routerend(False)

    # logを書き込み
    json_str = json.dumps(log)
    with log_path.open(mode="w") as conf:
        conf.write(json_str)

    # プロジェクトディレクトリを作成
    file_name = str(log["file_list"][-1])
    current_project_folder_path = config.FILES_PATH / file_name
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
    files_dir = [fd.name for fd in config.FILES_PATH.iterdir() if fd.is_dir()]
    project_files = [pf.name for pf in current_project_folder_path.iterdir()]

    files_dir.sort(key=int)
    project_files.sort()

    return {"tmp_files_projects": files_dir, "project_files": project_files, "log": log}


@router.get("/project-list", summary="projectのリストを返却します", tags=["files"], status_code=200)
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
    log_path = config.FILES_PATH / "log"

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
    current_project_folder_path = config.FILES_PATH / file_name

    # プロジェクトディレクトリの内容を取得
    files_dir = [fd.name for fd in config.FILES_PATH.iterdir() if fd.is_dir()]
    project_files = [pf.name for pf in current_project_folder_path.iterdir()]

    files_dir.sort(key=int)
    project_files.sort()

    return {"tmp_files_projects": files_dir, "log": log}


@router.get("/project", summary="projectのフォルダ内容を返却します", tags=["files"])
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

    log_path = config.FILES_PATH / "log"

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
    current_project_folder_path = config.FILES_PATH / file_name

    # プロジェクトディレクトリの内容を取得
    project_files = [pf.name for pf in current_project_folder_path.iterdir()]
    project_files.sort()

    return {"project_files": project_files}


@router.delete("/deletefiles", summary="tmp_imageの中身を削除", tags=["files"], status_code=200)
def run_deletefiles():

    for f in config.IMAGES_PATH.glob("*.png"):
        if f.is_file:
            f.unlink()


@router.put("/copy", summary="プロジェクトから「tmp_image」へpng画像コピー", tags=["files"])
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
            shutil.copy(f, config.IMAGES_PATH)

    file_list = []
    for i in config.IMAGES_PATH.glob("*.png"):
        file_list.routerend(i.name)
    file_list.sort()

    return {"result": file_list}


@router.put("/memo", summary="outputを出力", tags=["files"])
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


@router.get("/memo", summary="memoを取得", tags=["files"])
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


@router.get("/memo_manual", summary="memo_manualを取得", tags=["files"])
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
        memo_manual.routerend(result)

    return {"memo_manual": memo_manual}


@router.get("/final_all", summary="final_allを取得", tags=["files"])
def get_finalall(pj: int = -1):

    final_all_path = pj_path(pj) / "final_all.txt"

    if not final_all_path.is_file():
        raise HTTPException(status_code=404)

    with final_all_path.open() as f:
        result = f.read()

    if result == "":
        raise HTTPException(status_code=404)

    return {"finalall": result}


@router.get("/progress", summary="progress.txtに記載の進捗率などの情報を取得", tags=["files"])
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


@router.get(
    "/time_list",
    summary="画像の時刻リストが記載されたformatted_time_list.txtの内容を配列で取得",
    tags=["files"],
)
def get_time_list(pj: int = -1):
    time_list_path = pj_path(pj) / "formatted_time_list.txt"

    if not time_list_path.is_file():
        raise HTTPException(status_code=404)

    with time_list_path.open() as f:
        result = f.readlines()

    for i in range(len(result)):
        result[i] = result[i].rstrip("\n")

    return {"result": result}


@router.get("/manual_delete_list", summary="manual_delete_list.txtを取得", tags=["files"])
def get_manual_delete_list(pj: int = -1):
    # fmt: off
    """
    manual_delete_list.txtを取得します。

    __body__

    ```JSON
    [
        ["H000005", "0"],
        ["H000005", "3"],
        ["H000012", "3"],
    ]
    ```
    """ # noqa
    # fmt: on

    manual_delete_path = pj_path(pj) / "manual_delete_list.txt"

    if not manual_delete_path.is_file():
        raise HTTPException(status_code=404)

    with manual_delete_path.open() as f:
        result = f.read()

    result = split_list(result.split(), 2)

    return {"result": result}


