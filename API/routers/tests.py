from fastapi import APIRouter
from fastapi.responses import HTMLResponse


router = APIRouter(
    prefix="/test",
    tags=["tests"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", summary="ファイルアップロード確認用", tags=["tests"])
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
