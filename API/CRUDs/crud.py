from API.models.dir_structure import DirStructure
from API.database import session


def get_tract():
    # "SELECT this_dir_id,this_dir_name,n_total_images,n_measured_images FROM dir_structure WHERE level=2"
    queryResult = session.query(DirStructure.this_dir_id, DirStructure.this_dir_name, DirStructure.n_total_images, DirStructure.n_measured_images).filter(DirStructure.level == 2)

    tmpResult = {}
    for aQueryResult in queryResult:
        tractId = aQueryResult["this_dir_name"]
        if tractId in tmpResult:
            nTotalImages = tmpResult[tractId]["n_total_images"]
            nMeasuredImages = tmpResult[tractId]["n_measured_images"]
        else:
            nTotalImages = 0
            nMeasuredImages = 0
        nTotalImages += aQueryResult["n_total_images"]
        nMeasuredImages += aQueryResult["n_measured_images"]
        tmpResult[tractId] = {
            "n_total_images": nTotalImages,
            "n_measured_images": nMeasuredImages,
        }

    result = {}
    for key in tmpResult.keys():
        progress = (
            tmpResult[key]["n_measured_images"] / tmpResult[key]["n_total_images"]
        )
        result[key] = {"progress": progress}