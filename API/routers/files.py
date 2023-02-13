import shutil
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile
from API.utils import pj_path, split_list, convertFits2PngCoords, errorHandling
import API.config as config
import print_detailed_log
import COIAS_MySQL
import os
import traceback
import itertools
from CRUDs import crud


router = APIRouter(
    tags=["files"],
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


@router.post("/uploadfiles", summary="fileアップロード", tags=["files"])
async def create_upload_files(
    files: list[UploadFile] = None, doUploadFiles: bool = False
):
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
    log["file_list"].append(last_project)
    log["create_time"].append(dt)
    log["zip_upload"].append(False)

    # logを書き込み
    json_str = json.dumps(log)
    with log_path.open(mode="w") as conf:
        conf.write(json_str)

    # プロジェクトディレクトリを作成
    file_name = str(log["file_list"][-1])
    current_project_folder_path = config.FILES_PATH / file_name
    current_project_folder_path.mkdir()

    # fileを保存
    if doUploadFiles:
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
        file_list.append(i.name)
    file_list.sort()

    return {"result": file_list}


@router.put("/memo", summary="outputを出力", tags=["files"])
def run_memo(output_list: list, pj: int = -1):
    # fmt: off
    """
    フロントから渡されたbodyの配列からmemo.txtを出力します。

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
    memo.txtの内容を取得してフロントに返却します。

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
    memo_manual.txtの内容を取得してフロントに返却します。

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
        readResult = f.read()

    if readResult == "":
        raise HTTPException(status_code=404)

    memo_manual = []
    for line in readResult.split("\n"):
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


@router.put(
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


@router.put("/get_mpc", summary="2回目以降にレポートモードに入ったときにsend_mpcを取得するだけのAPI", tags=["files"])
def get_mpc(pj: int = -1):
    send_path = pj_path(pj) / "send_mpc.txt"
    result = ""

    with send_path.open(mode="r") as f:
        result = f.read()

    if not send_path.is_file():
        raise HTTPException(status_code=404)

    return {"send_mpc": result}


@router.get(
    "/final_disp", summary="最終確認モードで表示させる天体一覧を記したfinal_disp.txtを取得する", tags=["files"]
)
def get_finaldisp(pj: int = -1):
    final_disp_path = pj_path(pj) / "final_disp.txt"

    if not final_disp_path.is_file():
        raise HTTPException(status_code=404)

    with final_disp_path.open() as f:
        result = f.read()

    result = split_list(result.split(), 4)

    return {"result": result}


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


@router.get(
    "/predicted_disp",
    summary="直近の測定データから予測された天体の位置を記載したpredicted_disp.txtを取得する",
    tags=["files"],
)
def get_predicted_disp(pj: int = -1):
    predicted_disp_path = pj_path(pj) / "predicted_disp.txt"

    if not predicted_disp_path.is_file():
        raise HTTPException(status_code=404)

    with predicted_disp_path.open() as f:
        result = f.read()

    result = split_list(result.split(), 5)

    return {"result": result}


@router.get(
    "/AstMPC_refreshed_time",
    summary="小惑星軌道データが最後にダウンロードされAstMPC.edbが更新された日時を取得する",
    tags=["files"],
)
def get_AstMPC_refreshed_time(pj: int = -1):
    AstMPC_path = config.COIAS_PARAM_PATH / "AstMPC.edb"

    if not AstMPC_path.is_file():
        result = "小惑星軌道データが存在しません.「小惑星データ更新」ボタンを押して下さい."
    else:
        modified_unix_time = os.path.getmtime(AstMPC_path)
        dt = datetime.fromtimestamp(modified_unix_time)
        result = dt.strftime("最終更新: %Y年%m月%d日%H時")

    return {"result": result}


@router.get("/manual_delete_list", summary="manual_delete_list.txtを取得", tags=["files"])
def get_manual_delete_list(pj: int = -1):
    # fmt: off
    """
    manual_delete_list.txtの内容を取得しフロントに返却します。

    __body__

    ```
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


@router.put("/manual_delete_list", summary="manual_delete_list.txtの出力", tags=["files"])
def run_manual_delete_list(output_list: list, pj: int = -1):
    # fmt: off
    """
    フロントから受け取ったbodyの配列からmanual_delete_list.txtを出力します。

    __body__

    ```
    [
        "H000005 0",
        "H000005 3",
        "H000012 3",
    ]
    ```
    """ # noqa
    # fmt: on
    result = ""
    manual_delete_path = pj_path(pj) / "manual_delete_list.txt"

    with manual_delete_path.open(mode="w") as f:
        for line in output_list:
            f.write(line + "\n")

    with manual_delete_path.open(mode="r") as f:
        result = f.read()

    return {"manual_delete_list.txt": result}


@router.get(
    "/tract_list",
    summary="MySQLのCOIASデータベースに保存されている画像のtract一覧を取得する. 返り値はtractId(string)をキーとするオブジェクトで, 各キーの値であるオブジェクトは解析進捗率progress(float)をプロパティに持つ",
    tags=["files"],
)
def get_tract_list(pj: int = -1):
    try:
        os.chdir(pj_path(pj).as_posix())

        result = crud.get_tract()

    except Exception:
        log_path = pj_path(pj) / "log.txt"
        with log_path.open("w") as f:
            f.write("Some errors occur in select image mode!")
            f.write(traceback.format_exc())
            f.flush()
        print_detailed_log.print_detailed_log(dict(globals()))
        errorHandling(95)
    else:
        return {"result": result}


@router.get(
    "/patch_list",
    summary="int型で与えられたtractIdをクエリパラメータとして受け取り, そのtract以下に存在する全てのpatchを検索する. 返り値は'[tract]-[patch],[patch]'の文字列をキーとするオブジェクトで, 各キーの値であるオブジェクトは解析進捗率progress(float)をプロパティに持つ",
    tags=["files"],
)
def get_patch_list(tractId: int, pj: int = -1):
    try:
        os.chdir(pj_path(pj).as_posix())

        connection, cursor = COIAS_MySQL.connect_to_COIAS_database()
        cursor.execute(
            f"SELECT this_dir_id,this_dir_name,n_total_images,n_measured_images FROM dir_structure WHERE level=3 AND parent_dir_name='{tractId}'"
        )
        queryResult = cursor.fetchall()
        COIAS_MySQL.close_COIAS_database(connection, cursor)

        tmpResult = {}
        for aQueryResult in queryResult:
            patchId = aQueryResult["this_dir_name"]
            if patchId in tmpResult:
                nTotalImages = tmpResult[patchId]["n_total_images"]
                nMeasuredImages = tmpResult[patchId]["n_measured_images"]
            else:
                nTotalImages = 0
                nMeasuredImages = 0
            nTotalImages += aQueryResult["n_total_images"]
            nMeasuredImages += aQueryResult["n_measured_images"]
            tmpResult[patchId] = {
                "n_total_images": nTotalImages,
                "n_measured_images": nMeasuredImages,
            }

        result = {}
        for key in tmpResult.keys():
            progress = (
                tmpResult[key]["n_measured_images"] / tmpResult[key]["n_total_images"]
            )
            result[key] = {"progress": progress}

    except Exception:
        log_path = pj_path(pj) / "log.txt"
        with log_path.open("w") as f:
            f.write("Some errors occur in select image mode!")
            f.write(traceback.format_exc())
            f.flush()
        print_detailed_log.print_detailed_log(dict(globals()))
        errorHandling(95)
    else:
        return {"result": result}


@router.get(
    "/observe_date_list",
    summary="'[tract]-[patch],[patch]'の文字列をクエリパラメータとして受け取り, その[tract]-[patch],[patch]以下に存在する全ての観測日を取得する. 返り値は'yyyy-mm-dd'の文字列をキーとするオブジェクトで, 各キーの値であるオブジェクトは解析進捗率progress(float)とそのディレクトリid dir_id(int)をプロパティに持つ",
    tags=["files"],
)
def get_observe_date_list(patchId: str, pj: int = -1):
    try:
        os.chdir(pj_path(pj).as_posix())

        connection, cursor = COIAS_MySQL.connect_to_COIAS_database()
        cursor.execute(
            f"SELECT this_dir_id,this_dir_name,n_total_images,n_measured_images FROM dir_structure WHERE level=4 AND parent_dir_name='{patchId}'"
        )
        queryResult = cursor.fetchall()
        COIAS_MySQL.close_COIAS_database(connection, cursor)

        result = {}
        for aQueryResult in queryResult:
            progress = (
                aQueryResult["n_measured_images"] / aQueryResult["n_total_images"]
            )
            result[aQueryResult["this_dir_name"]] = {
                "progress": progress,
                "dir_id": aQueryResult["this_dir_id"],
            }

    except Exception:
        log_path = pj_path(pj) / "log.txt"
        with log_path.open("w") as f:
            f.write("Some errors occur in select image mode!")
            f.write(traceback.format_exc())
            f.flush()
        print_detailed_log.print_detailed_log(dict(globals()))
        errorHandling(95)
    else:
        return {"result": result}


@router.get(
    "/image_list",
    summary="選択した画像を格納しているディレクトリ構造の末端のディレクトリid (str, 複数可能・複数の時は-で区切られる)をクエリパラメータとして受け取り, そのディレクトリ以下に存在する画像の一覧を取得する. 返り値は画像ファイル名をキーとするオブジェクトで, 各キーの値であるオブジェクトは自動測定済みであるか否かを示すisAutoMeasured(bool)と手動測定済みであるか否かを示すisManualMeasured(bool)をプロパティに持つ",
    tags=["files"],
)
def get_image_list(dirIdsStr: str, pj: int = -1):
    try:
        os.chdir(pj_path(pj).as_posix())

        dirIds = []
        dirIdsSplitted = dirIdsStr.split("-")
        for dirIdStr in dirIdsSplitted:
            dirIds.routerend(int(dirIdStr))

        connection, cursor = COIAS_MySQL.connect_to_COIAS_database()
        result = {}

        for dirId in dirIds:
            cursor.execute(
                f"SELECT image_id,image_name,is_auto_measured,is_manual_measured FROM image_info WHERE direct_parent_dir_id={dirId}"
            )
            queryResult = cursor.fetchall()

            for aQueryResult in queryResult:
                result[aQueryResult["image_name"]] = {
                    "isAutoMeasured": (aQueryResult["is_auto_measured"] == 1),
                    "isManualMeasured": (aQueryResult["is_manual_measured"] == 1),
                }

        COIAS_MySQL.close_COIAS_database(connection, cursor)

    except Exception:
        log_path = pj_path(pj) / "log.txt"
        with log_path.open("w") as f:
            f.write("Some errors occur in select image mode!")
            f.write(traceback.format_exc())
            f.flush()
        print_detailed_log.print_detailed_log(dict(globals()))
        errorHandling(95)
    else:
        return {"result": result}


@router.get(
    "/suggested_images",
    summary="画像をお勧め順に自動選択し、その画像のファイル名一覧([fileNames]), 赤経deg(ra)、赤緯deg(dec)、[tract]-[patch],[patch](tractPatch)、観測日(observeDate)をプロパティに持つオブジェクトを返す",
    tags=["files"],
)
def get_suggested_images(pj: int = -1):
    try:
        os.chdir(pj_path(pj).as_posix())

        # suggest condition 1: 黄道に近い領域1と2を先にお勧めして、黄道から遠い領域3は後回し
        conditions1 = ["dec_lowest<30", "dec_lowest>30"]
        # suggest condition 2: 年が最近のものほど優先
        conditions2 = []
        for year in range(2020, 2013, -1):
            conditions2.append(f"this_dir_name LIKE '{year}-%'")
        # suggest condition 3: 画像枚数が5枚のものを優先、次に4枚、その次にそれ以外
        conditions3 = ["n_total_images=5", "n_total_images=4", "n_total_images>5"]

        # ---get a directory for suggestion-----------------------------------
        connection, cursor = COIAS_MySQL.connect_to_COIAS_database()
        dirNotFound = True
        for condition1, condition2, condition3 in itertools.product(
            conditions1, conditions2, conditions3
        ):
            cursor.execute(
                f"SELECT IF (ra_lowest<45, ra_lowest, ra_lowest-360) AS ra_reduced, ra_lowest, dec_lowest, this_dir_id, parent_dir_name, this_dir_name FROM dir_structure WHERE level=4 AND n_measured_images=0 AND {condition1} AND {condition2} AND {condition3} ORDER BY this_dir_name DESC, ra_reduced DESC LIMIT 1;"
            )
            dirStructureQueryResults = cursor.fetchall()
            if len(dirStructureQueryResults) == 1:
                dirNotFound = False
                break

        if dirNotFound:
            raise FileNotFoundError("We cannot find any directory for suggestion")

        queryResult = dirStructureQueryResults[0]
        dirId = queryResult["this_dir_id"]
        ra = queryResult["ra_lowest"]
        dec = queryResult["dec_lowest"]
        observeDate = queryResult["this_dir_name"]
        tractPatch = queryResult["parent_dir_name"]
        # ---------------------------------------------------------------------

        # ---get image names in the suggested directory------------------------
        cursor.execute(
            f"SELECT image_name FROM image_info WHERE direct_parent_dir_id={dirId};"
        )
        imageInfoQueryResults = cursor.fetchall()
        if len(imageInfoQueryResults) < 4:
            raise Exception(
                f"Something wrong. Image number in the selected directory is smaller than 4: NImages={len(imageInfoQueryResults)}"
            )
        fileNames = []
        for aQueryResult in imageInfoQueryResults:
            fileNames.append(aQueryResult["image_name"])
        COIAS_MySQL.close_COIAS_database(connection, cursor)
        # ----------------------------------------------------------------------

        result = {
            "fileNames": fileNames,
            "ra": ra,
            "dec": dec,
            "tractPatch": tractPatch,
            "observeDate": observeDate,
        }

    except FileNotFoundError as e:
        print(e)
        raise HTTPException(status_code=404)
    except Exception:
        log_path = pj_path(pj) / "log.txt"
        with log_path.open("w") as f:
            f.write("Some errors occur in select image mode!")
            f.write(traceback.format_exc())
            f.flush()
        print_detailed_log.print_detailed_log(dict(globals()))
        errorHandling(95)
    else:
        return {"result": result}


@router.put(
    "/put_image_list",
    summary="解析したい画像ファイル名のリストをリクエストボディで受け取り, それら画像へのfull pathを作業ディレクトリのselected_warp_files.txtに書き出す",
    tags=["files"],
)
def put_image_list(imageNameList: list[str], pj: int = -1):
    try:
        os.chdir(pj_path(pj).as_posix())

        image_list_path = pj_path(pj) / "selected_warp_files.txt"

        connection, cursor = COIAS_MySQL.connect_to_COIAS_database()
        imageFullPathList = []
        for imageName in imageNameList:
            cursor.execute(
                f"SELECT full_dir FROM image_info WHERE image_name='{imageName}'"
            )
            queryResult = cursor.fetchall()
            if len(queryResult) == 0:
                print(f"record for the file {imageName} is not found!")
                raise FileNotFoundError
            elif len(queryResult) >= 2:
                print(
                    f"something wrong! There are multiple records for the image {imageName}: N records = {len(queryResult)}"
                )
                raise Exception
            else:
                imageFullPath = queryResult[0]["full_dir"] + "/" + imageName + "\n"
                imageFullPathList.append(imageFullPath)
        COIAS_MySQL.close_COIAS_database(connection, cursor)

        with image_list_path.open(mode="w") as f:
            f.writelines(imageFullPathList)

    except Exception:
        log_path = pj_path(pj) / "log.txt"
        with log_path.open("w") as f:
            f.write("Some errors occur in select image mode!")
            f.write(traceback.format_exc())
            f.flush()
        print_detailed_log.print_detailed_log(dict(globals()))
        errorHandling(95)
