from fastapi import APIRouter, Depends, UploadFile, File, status, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import shutil
import os
import uuid

from app.api.deps import db_dependency, get_current_user
from app.models.models import FileManage, Users
from app.schemas.schemas import FileDetail

router = APIRouter(prefix="/files", tags=["manage_files"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    db: db_dependency,
    current_user: Users = Depends(get_current_user),
    file: UploadFile = File(...),
):
    upload_dir = "uploaded_files"
    os.makedirs(upload_dir, exist_ok=True)

    file_extension = os.path.splitext(file.filename)[1]
    stored_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, stored_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)

    new_file = FileManage(
        user_id=current_user.id,
        filename=file.filename,
        stored_filename=stored_filename,
        file_type=file.content_type,
        file_size=file_size,
        path=file_path,
    )

    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    return {"message": f"'{file.filename}' uploaded successfully"}


@router.get("/list", status_code=status.HTTP_200_OK, response_model=list[FileDetail])
async def list_files(
    db: db_dependency,
    current_user: Users = Depends(get_current_user),
    filename: str = None,
):
    if filename:
        files = (
            db.query(FileManage)
            .filter(
                FileManage.user_id == current_user.id,
                FileManage.filename.ilike(f"%{filename}%"),
            )
            .all()
        )
        if not files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This file cannot be found",
            )
        return files

    if not filename:
        files = db.query(FileManage).filter(FileManage.user_id == current_user.id).all()
        if not files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You have no files uploaded",
            )
    return files


@router.get("/download/{filename}", status_code=status.HTTP_200_OK)
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
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )

    file_path = file_record.path
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found on server"
        )

    # Increment download count
    file_record.download_count += 1
    db.commit()

    return FileResponse(
        path=file_path, filename=file_record.filename, media_type=file_record.file_type
    )


@router.delete("/delete/{filename}", status_code=status.HTTP_200_OK)
async def delete_file(
    filename: str, db: db_dependency, current_user: Users = Depends(get_current_user)
):
    file_record = (
        db.query(FileManage)
        .filter(FileManage.filename == filename, FileManage.user_id == current_user.id)
        .first()
    )

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )

    file_path = file_record.path
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(file_record)
    db.commit()

    return {"message": f"File '{filename}' deleted successfully"}
