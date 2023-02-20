from fastapi import APIRouter, Depends
from API.dependencies import get_token_header


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_token_header)],
    responses={418: {"description": "I'm a teapot"}},
)


@router.get("/")
async def message_for_admin():
    return {"message": "Hello admin user"}