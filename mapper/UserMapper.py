from datetime import datetime

from sqlalchemy import text,select
from sqlmodel import Session

from config import engine
from pojo.User import UserCreate, User, UserRead, UserUpdate


class UserMapper:

    @staticmethod
    def to_read(user: User) -> UserRead:
        """ORM -> UserRead"""
        return UserRead.model_validate(user)

    @staticmethod
    def from_create(user_create: UserCreate) -> User:
        """UserCreate -> ORM"""
        return User(
            name=user_create.name,
            password=user_create.password,
        )

    @staticmethod
    def apply_update(user: User, user_update: UserUpdate) -> User:
        """在已有 ORM 对象上应用更新"""
        if user_update.name is not None:
            user.name = user_update.name
        if user_update.password is not None:
            user.password = user_update.password
        user.update_at = datetime.utcnow()
        return user

    @staticmethod
    def create(name:str,password:str) -> UserRead:
        with Session(engine) as session:
            user_create = UserCreate(name=name, password=password)
            user = UserMapper.from_create(user_create)  # 转成 ORM
            session.add(user)
            session.commit()
            session.refresh(user)
            return UserMapper.to_read(user)
    @staticmethod
    def update(user:User,name:str,password:str) -> UserRead:
        with Session(engine) as session:
            update_data = UserUpdate(name=name, password=password) if password else UserUpdate(name=name)
            UserMapper.apply_update(user, update_data)
            session.add(user)
            session.commit()
            return UserMapper.to_read(user)
    @staticmethod
    def findbyname(name:str) -> UserRead | None:
        with Session(engine) as session:
            stmt = select(User).where(text("name=:name"))
            users = session.exec(stmt.params(name=name)).all()
        return UserMapper.to_read(users) if users else None

    @staticmethod
    def findbyid(id:int) -> UserRead | None:
        with Session(engine) as session:
            stmt = select(User).where(text("id=:id"))
            users = session.exec(stmt.params(id=id)).all()
        return UserMapper.to_read(users) if users else None
