from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from Database.data import SessionLocal
from authentication.token import decode_verification_token
from Database.models import Users
from typing import Annotated
from fastapi.responses import HTMLResponse

router = APIRouter(
    tags=["authentication"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/verify", response_class=HTMLResponse)
def verify_email(token: str, db: db_dependency):
    try:
        email = decode_verification_token(token)
        if not email:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token payload")
    except Exception as e:
        return """
        <html>
            <head>
                <title>Verification Failed</title>
            </head>
            <body style="display: flex; justify-content: center; align-items: center; height: 100vh; font-family: Arial, sans-serif; background-color: #f4f4f4;">
                <div style="text-align: center; padding: 40px; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h1 style="color: #dc3545;">Verification Failed</h1>
                    <p>The verification link is invalid or has expired.</p>
                </div>
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
            <body style="display: flex; justify-content: center; align-items: center; height: 100vh; font-family: Arial, sans-serif; background-color: #f4f4f4;">
                <div style="text-align: center; padding: 40px; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h1 style="color: #dc3545;">User Not Found</h1>
                    <p>We could not find a user associated with this email.</p>
                </div>
            </body>
        </html>
        """

    if user.is_verified:
        return """
        <html>
            <head>
                <title>Already Verified</title>
            </head>
            <body style="display: flex; justify-content: center; align-items: center; height: 100vh; font-family: Arial, sans-serif; background-color: #f4f4f4;">
                <div style="text-align: center; padding: 40px; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h1 style="color: #0275d8;">Already Verified</h1>
                    <p>Your email has already been verified. You can proceed to login.</p>
                </div>
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
        <body style="display: flex; justify-content: center; align-items: center; height: 100vh; font-family: Arial, sans-serif; background-color: #f4f4f4;">
            <div style="text-align: center; padding: 40px; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h1 style="color: #28a745;">Verification Successful!</h1>
                <p>Your email has been successfully verified.</p>
                <p>You can now close this window and log in to your account.</p>
            </div>
        </body>
    </html>
    """
