from pydantic import BaseModel
from datetime import datetime

#Registration schema
class RegisterUser(BaseModel):
    first_name: str
    last_name: str
    middle_name: str | None = None
    email: str
    password: str
    confirm_password: str
    
    
#Token schema
class Token(BaseModel):
    message: str | None = None
    token_type: str
    access_token: str
   
   
class LoginUser(BaseModel):
    email: str
    password: str
    

class UserResponse(BaseModel):
    first_name: str
    last_name: str
    middle_name: str | None = None
    email: str
    

    class Config:
        from_attributes = True
    
    
class TokenData(BaseModel):
    username: str | None = None
    

class FileDetail(BaseModel):
    filename: str
    file_type: str
    file_size: int
    uploaded_at: datetime | None = None
    download_count: int

    class Config:
        from_attributes = True
     