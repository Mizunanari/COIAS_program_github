import json
import traceback
from fastapi import HTTPException
from astropy.io import fits
from PIL import Image
import API.config as config


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

    log_path = config.FILES_PATH / "log"

    path = ""

    if log_path.is_file():
        with log_path.open(mode="r") as conf:
            conf_json = conf.read()

        if not conf_json == "":
            log = json.loads(conf_json)
        else:
            return

        file_name = log["file_list"][pj]
        path = config.FILES_PATH / str(file_name)
    elif is_websocket:
        path = config.FILES_PATH / ""
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
        elif numString[-2] == "9":
            errorList.update({"place": "画像選択"})
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
                    "reason": "予期せぬエラーが発生しました。数回やり直してもエラーが出る場合、開発者にlog.txtをメールで送信して下さい。「ログをダウンロード」ボタンからlog.txtをダウンロードできます。"
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
