from schema import RegisterUser, UserResponse
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from typing import Annotated
from fastapi import APIRouter, Depends
from Database.models import Users
from Database.data import SessionLocal
from sqlalchemy.orm import Session
from fastapi import status
from authentication.email import send_verification_email


router = APIRouter(
    prefix="/auth",
    tags=["authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth_2_schemes = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
db_dependency = Annotated[Session, Depends(get_db)]
@router.post('/register')
async def create_user(db: db_dependency, create_user_request: RegisterUser):
    if create_user_request.password != create_user_request.confirm_password:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Password and Confirm Password do not match"
        }
    
    existing_user = db.query(Users).filter(Users.email == create_user_request.email).first()
    if existing_user:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Email already registered"
        }

    create_user_model = Users(
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        middle_name=create_user_request.middle_name,
        email=create_user_request.email,
        hashed_password = pwd_context.hash(create_user_request.password)
    )
    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)
    user_response = UserResponse.model_validate(create_user_model)
   
    await send_verification_email(create_user_model.email, create_user_model.first_name)
    
    return {
            "status": status.HTTP_201_CREATED,
            "message": user_response
        }

    