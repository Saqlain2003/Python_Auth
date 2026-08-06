import os
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

# Load sensitive keys securely from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_insecure_key_for_local_dev_only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Matches the exact route path we will use for handling logins
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against its hashed database version safely."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), 
        hashed_password.encode("utf-8")
    )

def get_password_hash(password: str) -> str:
    """Generates a secure bcrypt password hash string."""
    return bcrypt.hashpw(
        password.encode("utf-8"), 
        bcrypt.gensalt()
    ).decode("utf-8")

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generates a signed JWT access token containing arbitrary payload data."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], 
    db: Annotated[Session, Depends(get_db)]
) -> models.User:
    """Dependency to validate JWT from headers and extract the current active database user."""
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")  # Industry standard uses email/ID as subject

        if email is None:
            raise credential_exception
            
        token_data = schemas.TokenData(email=email)
    except jwt.PyJWTError:  # Explicitly catches PyJWT validation issues safely
        raise credential_exception

    # Querying by email is faster and more production-secure than username lookup
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credential_exception

    return user