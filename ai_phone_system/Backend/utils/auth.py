from fastapi import Depends, HTTPException, Request
import jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET", "dev_secret")
ALGORITHM = "HS256"


def get_current_business_id(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="Missing token")

    token = auth.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        business_id = payload.get("business_id")
        if not business_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return business_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")