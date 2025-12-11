from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from typing import Annotated
from fastapi import APIRouter, Depends
from Database.models import Users
from sqlalchemy.orm import Session
from schema import LoginUser, Token
from authentication.token import create_access_token
from fastapi import HTTPException, status
from Database.data import SessionLocal

router = APIRouter(prefix="/auth", tags=["authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth_2_schemes = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


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
