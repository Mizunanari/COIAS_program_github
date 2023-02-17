from fastapi import APIRouter, HTTPException
from API.utils import pj_path, errorHandling
import print_detailed_log
import COIAS_MySQL
import os
import traceback
import itertools
from API.CRUDs import crud


router = APIRouter(
    tags=["db"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/tract_list",
    summary="MySQLのCOIASデータベースに保存されている画像のtract一覧を取得する. 返り値はtractId(string)をキーとするオブジェクトで, 各キーの値であるオブジェクトは解析進捗率progress(float)をプロパティに持つ",
    tags=["db"],
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
    tags=["db"],
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
    tags=["db"],
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
    tags=["db"],
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
    tags=["db"],
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
    summary="解析したい画像ファイル名のリストをリクエストボディで受け取り, それら画像へのfull pathを作業ディレクトリのselected_warp_db.txtに書き出す",
    tags=["db"],
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
