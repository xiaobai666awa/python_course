from datetime import datetime
from typing import List, Dict

from sqlmodel import Session, select
from config import engine
from pojo.User import UserCreate, User, UserRead, UserUpdate

class UserMapper:

    @staticmethod
    def to_read(user: User) -> UserRead:
        return UserRead.model_validate(user)

    @staticmethod
    def from_create(user_create: UserCreate) -> User:
        return User(name=user_create.name, password=user_create.password)

    @staticmethod
    def apply_update(user: User, user_update: UserUpdate) -> User:
        if user_update.name is not None:
            user.name = user_update.name
        if user_update.password is not None:
            user.password = user_update.password
        user.update_at = datetime.utcnow()
        return user

    # ---------------- CRUD 操作 ----------------
    @staticmethod
    def create(name: str, password: str) -> UserRead:
        with Session(engine) as session:
            user_create = UserCreate(name=name, password=password)
            user = UserMapper.from_create(user_create)
            session.add(user)
            session.commit()
            session.refresh(user)
            return UserMapper.to_read(user)

    @staticmethod
    def update(user: User, name: str, password: str | None = None) -> UserRead:
        with Session(engine) as session:
            update_data = UserUpdate(name=name, password=password)
            UserMapper.apply_update(user, update_data)
            session.add(user)
            session.commit()
            session.refresh(user)
            return UserMapper.to_read(user)

    @staticmethod
    def find_by_name(name: str) -> User | None:
        with Session(engine) as session:
            stmt = select(User).where(User.name == name)
            user = session.exec(stmt).first()
            return user if user else None

    @staticmethod
    def find_by_id(id: int) -> User | None:
        with Session(engine) as session:
            stmt = select(User).where(User.id == id)
            user = session.exec(stmt).first()
            return user if user else None
    @staticmethod
    def bulk_insert(users: List[Dict[str, str]]) -> List[User]:
        """
        批量添加用户
        users: List[Dict], 每个 Dict 包含 'name' 和 'password'
        返回插入后的 User 对象列表
        """
        user_objects = [User(name=u["name"], password=u["password"]) for u in users]

        with Session(engine) as session:
            session.add_all(user_objects)  # 批量添加
            session.commit()               # 提交事务
            for user in user_objects:
                session.refresh(user)      # 刷新每个对象，获取自增主键
        return user_objects