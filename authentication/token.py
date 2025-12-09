from datetime import datetime, timedelta
from jose import jwt,   JWTError
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRES_AT
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException



def create_access_token(data: dict):
    expire = datetime.utcnow()+ timedelta(
        minutes=ACCESS_TOKEN_EXPIRES_AT
    )
    
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    
    token = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return token

def create_verification_token(email: str):
    return create_access_token({"sub": email})

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
def decode_verification_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        
        if email is None:
            raise HTTPException(status_code=404, detail="Invalid email")
        
        return email
    
    except JWTError:
        raise HTTPException(status_code=404, detail="Invalid email or token has expired")
