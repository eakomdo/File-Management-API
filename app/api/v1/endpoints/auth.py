from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import jwt, JWTError
import os

from app.api.deps import db_dependency
from app.models.models import Users
from app.schemas.schemas import (
    RegisterUser,
    LoginUser,
    Token,
    PasswordReset,
    NewPassword,
)
from app.core.security import create_access_token, decode_verification_token
from app.services.email import send_verification_email, send_password_reset_email
from app.core.config import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/auth", tags=["authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register")
async def create_user(db: db_dependency, create_user_request: RegisterUser):
    if create_user_request.password != create_user_request.confirm_password:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Password and Confirm Password do not match",
        }

    existing_user = (
        db.query(Users).filter(Users.email == create_user_request.email).first()
    )
    if existing_user:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Email already registered",
        }

    create_user_model = Users(
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        middle_name=create_user_request.middle_name,
        email=create_user_request.email,
        hashed_password=pwd_context.hash(create_user_request.password),
    )
    db.add(create_user_model)
    db.commit()

    await send_verification_email(create_user_model.email, create_user_model.first_name)
    return {
        "message": "User created successfully. Please check your email to verify your account."
    }


@router.post("/login", response_model=Token)
async def login_user(db: db_dependency, login_request: LoginUser):
    user = db.query(Users).filter(Users.email == login_request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
        )

    if not pwd_context.verify(login_request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
        )

    token = create_access_token(data={"sub": user.email, "id": user.id})
    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
    }


@router.post("/token", response_model=Token)
async def login_for_access_token(
    db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()
):
    user = db.query(Users).filter(Users.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials"
        )

    if not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials"
        )

    token = create_access_token(data={"sub": user.email, "id": user.id})
    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
    }


@router.get("/verify", response_class=HTMLResponse)
def verify_email(token: str, db: db_dependency):
    try:
        email = decode_verification_token(token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token payload"
            )
    except Exception:
        return """
        <html>
            <head>
                <title>Verification Failed</title>
            </head>
            <body>
                <h1>Verification Failed</h1>
                <p>The verification link is invalid or has expired.</p>
            </body>
        </html>
        """

    user = db.query(Users).filter(Users.email == email).first()

    if not user:
        return """
        <html>
            <head>
                <title>User Not Found</title>
            </head>
            <body>
                <h1>User Not Found</h1>
                <p>User associated with this token does not exist.</p>
            </body>
        </html>
        """

    if user.is_verified:
        return """
        <html>
            <head>
                <title>Already Verified</title>
            </head>
            <body>
                <h1>Already Verified</h1>
                <p>Your email is already verified.</p>
            </body>
        </html>
        """

    user.is_verified = True
    db.commit()

    return """
    <html>
        <head>
            <title>Verification Successful</title>
        </head>
        <body>
            <h1>Verification Successful</h1>
            <p>Your email has been successfully verified. You can now login.</p>
        </body>
    </html>
    """


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
    link = f"http://{domain}/auth/reset-password?token={token}"

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
