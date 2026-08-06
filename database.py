import os
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from a .env file
load_dotenv()

# Fetch database URL from environment with a fallback for local safety
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password@localhost:5432/fastapi_practice"
)

# Production-optimized engine configuration
engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # Keeps up to 20 persistent connections open
    max_overflow=10,       # Allows 10 extra temporary connections during traffic spikes
    pool_timeout=30,       # Aborts wait if connection takes over 30 seconds
    pool_recycle=1800,     # Refreshes connections every 30 minutes to prevent drops
)

# Session factory configuration
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# Declarative base class for models
Base = declarative_base()

# Context manager-compatible dependency injection
def get_db() -> Generator:
    """Provides a database session context for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
