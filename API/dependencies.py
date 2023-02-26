from fastapi import Header, HTTPException
import API.config as config


async def get_token_header(x_token: str = Header()):
    if x_token != config.X_TOKEN_HEADER:
        raise HTTPException(status_code=400, detail="X-Token header invalid")
