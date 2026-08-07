import os
from typing import Annotated
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
import schemas 
import auth
from database import engine, get_db  # Imported engine back in

# Load environment configuration
load_dotenv()

# Automatically create local database tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Local Production FastAPI Application", version="1.0.0")

# Pull CORS origins dynamically, fallback safely for local development
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

# Dedicated authentication router for clean architectural separation
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    user: schemas.UserCreate, 
    db: Annotated[Session, Depends(get_db)]
):
    """Registers a new, unique system user securely."""
    db_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Username or email is already registered."
        )

    hashed_pwd = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username, 
        email=user.email, 
        hashed_pass=hashed_pwd
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@auth_router.post("/login", response_model=schemas.Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: Annotated[Session, Depends(get_db)]
):
    """Authenticates user credentials and generates a secure JWT access token."""
    user = db.query(models.User).filter(
        (models.User.email == form_data.username) | (models.User.username == form_data.username)
    ).first()
    
    if not user or not auth.verify_password(form_data.password, user.hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.get("/users/me", response_model=schemas.UserOut)
async def read_user_me(
    current_user: Annotated[models.User, Depends(auth.get_current_user)]
):
    """Retrieves authenticated information for the currently active user context."""
    return current_user


# Include router references back into the primary application instance
app.include_router(auth_router)
