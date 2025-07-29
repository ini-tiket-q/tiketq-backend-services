import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from domain.repository import UserRepository
from domain.models import UserInDB

DATABASE_URL = os.getenv("AUTH_DB_URL")
if not DATABASE_URL:
    raise RuntimeError("AUTH_DB_URL environment variable is required")

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class UserTable(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class DBUserRepository(UserRepository):
    def get_user_by_email(self, email: str) -> UserInDB | None:
        with SessionLocal() as db:
            user = db.query(UserTable).filter(UserTable.email == email).first()
            if user:
                return UserInDB(email=user.email, password="", hashed_password=user.hashed_password)
            return None

    def create_user(self, user: UserInDB) -> None:
        with SessionLocal() as db:
            db_user = UserTable(email=user.email, hashed_password=user.hashed_password)
            db.add(db_user)
            db.commit()
