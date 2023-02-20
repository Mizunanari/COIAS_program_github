# .env ファイルをロードして環境変数へ反映
from dotenv import load_dotenv
import pathlib
import os
import PARAM
load_dotenv()

OPT_PATH = pathlib.Path(os.getenv("OPT_PATH"))
PROGRAM_PATH = OPT_PATH / os.getenv("PROGRAM_PATH")
IMAGES_PATH = OPT_PATH / os.getenv("IMAGES_PATH")
FILES_PATH = OPT_PATH / os.getenv("FILES_PATH")
SUBARU_PATH = PROGRAM_PATH / os.getenv("SUBARU_PATH")
DOC_IMAGE_PATH = PROGRAM_PATH / os.getenv("DOC_IMAGE_PATH")
COIAS_PARAM_PATH = pathlib.Path(PARAM.COIAS_DATA_PATH + os.getenv("COIAS_PARAM_PATH"))

WEB_ORIGINS = os.getenv("WEB_ORIGINS").split(",")
X_TOKEN_HEADER = os.getenv("X_TOKEN_HEADER")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_DATABASE_NAME = os.getenv("DB_DATABASE_NAME")
DB_USER_NAME = os.getenv("DB_USER_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
