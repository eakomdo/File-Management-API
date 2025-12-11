from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Annotated
from Database.data import SessionLocal
from Database.models import FileManage, Users
from authentication.token import oauth2_scheme
from jose import jwt, JWTError
from config import SECRET_KEY, ALGORITHM
import os

router = APIRouter(prefix="/auth", tags=["manage_files"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: db_dependency
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("id")
        if email is None or user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(Users).filter(Users.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


@router.get("/file/download/{filename}", status_code=status.HTTP_200_OK)
async def download_file(
    filename: str, db: db_dependency, current_user: Users = Depends(get_current_user)
):
    file_record = (
        db.query(FileManage)
        .filter(FileManage.filename == filename, FileManage.user_id == current_user.id)
        .first()
    )

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File doesn't exist"
        )

    if not os.path.exists(file_record.path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found on server"
        )

    file_record.download_count += 1
    db.commit()

    return FileResponse(
        path=file_record.path,
        filename=file_record.filename,
        media_type=file_record.file_type,
    )
