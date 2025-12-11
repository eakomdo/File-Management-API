from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from Database.data import SessionLocal
from Database.models import FileManage, Users
from authentication.token import oauth2_scheme
from jose import jwt, JWTError
from config import SECRET_KEY, ALGORITHM
from schema import FileDetail

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


# list all files uploaded by the user
@router.get(
    "/file/list", status_code=status.HTTP_200_OK, response_model=list[FileDetail]
)
async def list_file(db: db_dependency, current_user: Users = Depends(get_current_user)):
    query = db.query(FileManage).filter(FileManage.user_id == current_user.id)

    if query is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No files found or uploaded"
        )
    return query.all()


# search for a file using its filename
@router.get(
    "/file/list/{filename}",
    status_code=status.HTTP_200_OK,
    response_model=list[FileDetail],
)
async def list_file_filename(
    db: db_dependency, filename: str, current_user: Users = Depends(get_current_user)
):
    query = db.query(FileManage).filter(FileManage.user_id == current_user.id)

    if filename:
        filtered_query = query.filter(FileManage.filename == (filename))
        results = filtered_query.all()

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The file doesn't exist or check the spelling of the filename",
        )
    return results
