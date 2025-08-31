import os
from sqlalchemy import create_engine, Column, Integer, String, Enum as SQLEnum
from sqlalchemy.orm import sessionmaker, declarative_base
from domain.repository import UserRepository
from domain.models import UserInDB, UserRole
from typing import List

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
    role = Column(SQLEnum(UserRole), default=UserRole.USER)

class DBUserRepository(UserRepository):
    def get_user_by_email(self, email: str) -> UserInDB | None:
        with SessionLocal() as db:
            user = db.query(UserTable).filter(UserTable.email == email).first()
            if user:
                return UserInDB(
                    id=user.id,
                    email=user.email, 
                    password="", 
                    hashed_password=user.hashed_password,
                    role=user.role
                )
            return None

    def get_user_by_id(self, user_id: int) -> UserInDB | None:
        with SessionLocal() as db:
            user = db.query(UserTable).filter(UserTable.id == user_id).first()
            if user:
                return UserInDB(
                    id=user.id,
                    email=user.email, 
                    password="", 
                    hashed_password=user.hashed_password,
                    role=user.role
                )
            return None

    def create_user(self, user: UserInDB) -> UserInDB:
        with SessionLocal() as db:
            db_user = UserTable(
                email=user.email, 
                hashed_password=user.hashed_password,
                role=user.role
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return UserInDB(
                id=db_user.id,
                email=db_user.email,
                password="",
                hashed_password=db_user.hashed_password,
                role=db_user.role
            )

    def get_all_users(self) -> List[UserInDB]:
        with SessionLocal() as db:
            users = db.query(UserTable).all()
            return [
                UserInDB(
                    id=user.id,
                    email=user.email,
                    password="",
                    hashed_password=user.hashed_password,
                    role=user.role
                )
                for user in users
            ]

    def update_user_role(self, user_id: int, role: UserRole) -> UserInDB | None:
        with SessionLocal() as db:
            user = db.query(UserTable).filter(UserTable.id == user_id).first()
            if not user:
                return None
            
            user.role = role
            db.commit()
            db.refresh(user)
            return UserInDB(
                id=user.id,
                email=user.email,
                password="",
                hashed_password=user.hashed_password,
                role=user.role
            )
