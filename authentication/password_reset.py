from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from Database.data import SessionLocal
from Database.models import Users
from schema import PasswordReset, NewPassword
from authentication.token import create_access_token
from authentication.email import send_password_reset_email
from passlib.context import CryptContext
from typing import Annotated
from jose import jwt, JWTError
from config import SECRET_KEY, ALGORITHM
import os

router = APIRouter(prefix="/auth", tags=["authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/reset_password")
async def reset_password(email_data: PasswordReset, db: db_dependency):
    user = db.query(Users).filter(Users.email == email_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    token = create_access_token({"sub": user.email})

    user.password_reset_token = token
    db.commit()

    domain = os.getenv("DOMAIN", "localhost:8000")
    link = f"http://{domain}/reset-password?token={token}"

    await send_password_reset_email(user.email, link)

    return {"message": "Password reset email sent", "token": token}


@router.post("/confirm_password_reset")
async def confirm_password_reset(data: NewPassword, db: db_dependency):
    if data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
        )

    try:
        payload = jwt.decode(data.token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user = db.query(Users).filter(Users.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.password_reset_token != data.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )

    user.hashed_password = pwd_context.hash(data.new_password)
    user.password_reset_token = None
    db.commit()

    return {"message": "Password reset successfully"}
