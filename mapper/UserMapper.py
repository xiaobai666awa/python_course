from datetime import datetime
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
    def find_by_name(name: str) -> UserRead | None:
        with Session(engine) as session:
            stmt = select(User).where(User.name == name)
            user = session.exec(stmt).first()
            return UserMapper.to_read(user) if user else None

    @staticmethod
    def find_by_id(id: int) -> User | None:
        with Session(engine) as session:
            stmt = select(User).where(User.id == id)
            user = session.exec(stmt).first()
            return user if user else None
