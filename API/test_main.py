from API.main import app

from fastapi.testclient import TestClient
import API.config as config


client = TestClient(app)


def test_get_all_path():
    print(config.COIAS_PARAM_PATH)
    print(config.DOC_IMAGE_PATH)
    print(config.FILES_PATH)
    print(config.IMAGES_PATH)
    print(config.OPT_PATH)
    print(config.PROGRAM_PATH)
    print(config.SUBARU_PATH)
    print(config.WEB_ORIGINS)
    print(config.X_TOKEN_HEADER)


def test_get_trac_list():
    response = client.get("/tract_list")
    print(response)
    assert response.status_code == 200


if __name__ == "__main__":
    test_get_all_path()