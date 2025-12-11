from fastapi import APIRouter, Depends, status, HTTPException
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


@router.delete("/file/delete/{filename}", status_code=status.HTTP_200_OK)
async def delete_file(
    filename: str, db: db_dependency, current_user: Users = Depends(get_current_user)
):
    file_to_delete = (
        db.query(FileManage)
        .filter(FileManage.user_id == current_user.id, FileManage.filename == filename)
        .first()
    ) 
    
    if file_to_delete is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The file doesn't exist or type the appropriate file name")
    
    if file_to_delete.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    elif os.path.exists(file_to_delete.path):
        os.remove(file_to_delete.path)
        db.delete(file_to_delete)
        db.commit()

    return {"status": status.HTTP_200_OK, "message": "File deleted successfully"}
