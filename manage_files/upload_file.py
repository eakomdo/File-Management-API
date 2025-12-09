from fastapi import APIRouter, Depends, UploadFile, File, status, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from Database.data import SessionLocal
from Database.models import FileManage, Users
from authentication.token import oauth2_scheme
from jose import jwt, JWTError
from config import SECRET_KEY, ALGORITHM
import shutil
import os
import uuid

router = APIRouter(
    prefix="/auth",
    tags=["manage_files"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: db_dependency):
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

@router.post('/file/upload', status_code=status.HTTP_201_CREATED)
async def upload_file(db: db_dependency, current_user: dict = Depends(get_current_user), file: UploadFile = File(...)):
    upload_dir = "uploaded_files"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique filename to avoid collisions
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {str(e)}")
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    new_file = FileManage(
        user_id=current_user.id,
        filename=file.filename,
        stored_filename=unique_filename,
        file_type=file.content_type,
        file_size=file_size,
        path=file_path
    )
    
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    
    return {
        "status": status.HTTP_201_CREATED,
        "message": f"Your file, {file.filename} has been uploaded successfully",
        "data": {
            "id": new_file.id,
            "filename": new_file.filename,
            "size": new_file.file_size
        }
    }
