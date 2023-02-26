from fastapi import APIRouter, HTTPException
import os
import subprocess
from datetime import datetime
import API.config as config
from API.utils import pj_path, convertPng2FitsCoords, errorHandling, split_list


router = APIRouter(
    tags=["processes"],
    responses={404: {"description": "Not found"}},
)


@router.put("/memo_manual", summary="手動測定の出力", tags=["processes"])
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

    text = ""
    for (i, oldNewPair) in enumerate(modifiedList):
        text = text + "{} {}".format(oldNewPair[0], oldNewPair[1])
        if not i == len(modifiedList) - 1:
            text = text + "\n"
    text_path = pj_path(pj) / "manual_name_modify_list.txt"

    with text_path.open(mode="w") as f:
        f.write(text)


@router.put("/preprocess", summary="最新のMPCデータを取得", tags=["processes"], status_code=200)
def run_preprocess(pj: int = -1):

    os.chdir(pj_path(pj).as_posix())
    result = subprocess.run(["preprocess"])
    errorHandling(result.returncode)


@router.put("/startsearch2R", summary="ビニング&マスク", tags=["processes"], status_code=200)
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


@router.put(
    "/prempsearchC-before", summary="精密軌道取得 前処理", tags=["processes"], status_code=200
)
def run_prempsearchC_before(pj: int = -1):

    os.chdir(pj_path(pj).as_posix())
    result = subprocess.run(["prempsearchC-before"], shell=True)
    errorHandling(result.returncode)


@router.put("/prempsearchC-after", summary="精密軌道取得 後処理", tags=["processes"], status_code=200)
def run_prempsearchC_after(pj: int = -1):

    os.chdir(pj_path(pj).as_posix())
    result = subprocess.run(["prempsearchC-after"], shell=True)
    errorHandling(result.returncode)


@router.put("/astsearch_new", summary="自動検出", tags=["processes"], status_code=200)
def run_astsearch_new(pj: int = -1, nd: int = 4, ar: int = 6):

    os.chdir(pj_path(pj).as_posix())
    cmdStr = "astsearch_new nd={} ar={}".format(nd, ar)
    print(cmdStr)
    result = subprocess.run(cmdStr, shell=True)
    errorHandling(result.returncode)


@router.put(
    "/getMPCORB_and_mpc2edb", summary="出力ファイル整形", tags=["processes"], status_code=200
)
def run_getMPCORB_and_mpc2edb(pj: int = -1):

    os.chdir(pj_path(pj).as_posix())
    result = subprocess.run(["getMPCORB_and_mpc2edb_for_button"])
    errorHandling(result.returncode)


@router.put("/redisp", summary="再描画による確認作業", tags=["processes"])
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


@router.put(
    "/AstsearchR_between_COIAS_and_ReCOIAS",
    summary="探索モード後に走り自動検出天体の番号の付け替えを行う",
    tags=["processes"],
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


@router.put(
    "/AstsearchR_afterReCOIAS", summary="レポートモードに入ったとき発火し、send_mpcを作成", tags=["processes"]
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


@router.put(
    "/get_mpc", summary="2回目以降にレポートモードに入ったときにsend_mpcを取得するだけのAPI", tags=["processes"]
)
def get_mpc(pj: int = -1):
    send_path = pj_path(pj) / "send_mpc.txt"
    result = ""

    with send_path.open(mode="r") as f:
        result = f.read()

    if not send_path.is_file():
        raise HTTPException(status_code=404)

    return {"send_mpc": result}


@router.put("/AstsearchR_after_manual", summary="手動測定：再描画による確認作業", tags=["processes"])
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


@router.get(
    "/final_disp", summary="最終確認モードで表示させる天体一覧を記したfinal_disp.txtを取得する", tags=["processes"]
)
def get_finaldisp(pj: int = -1):
    final_disp_path = pj_path(pj) / "final_disp.txt"

    if not final_disp_path.is_file():
        raise HTTPException(status_code=404)

    with final_disp_path.open() as f:
        result = f.read()

    result = split_list(result.split(), 4)

    return {"result": result}


@router.get(
    "/predicted_disp",
    summary="直近の測定データから予測された天体の位置を記載したpredicted_disp.txtを取得する",
    tags=["processes"],
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
    tags=["processes"],
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


@router.put("/manual_delete_list", summary="manual_delete_list.txtの出力", tags=["processes"])
def run_manual_delete_list(output_list: list, pj: int = -1):
    """
    manual_delete_list.txtへ出力
    """

    # fmt: off
    """
    bodyの配列からmanual_delete_list.txtを出力します。

    __body__

    ```JSON
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
