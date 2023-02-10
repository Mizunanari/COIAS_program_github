from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from ..dependencies import get_token_header


router = APIRouter(
    prefix="/test",
    tags=["test"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", summary="ファイルアップロード確認用", tags=["test"])
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
