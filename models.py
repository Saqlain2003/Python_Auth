# Inside backend_auth/models.py (Your Submodule)
from sqlalchemy import Column, Integer, String
from database import Base

class UserMixin:
    """A reusable blueprint of user columns without a fixed database table"""
    id = Column(Integer, index=True, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_pass = Column(String)

class User(UserMixin, Base):
    """The default User table used by the submodule itself"""
    __tablename__ = "users"
