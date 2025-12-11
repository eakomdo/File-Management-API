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
                <p>We could not find a user associated with this email.</p>
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
                <p>Your email has already been verified. You can proceed to login.</p>
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
            <h1>Verification Successful!</h1>
            <p>Your email has been successfully verified.</p>
            <p>You can now close this window and log in to your account.</p>
        </body>
    </html>
    """
