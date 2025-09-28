from typing import Any

from mapper.UserMapper import UserMapper
from pojo.User import User, UserRead
from pojo.Result import Result
from utils.security import hash_password, verify_password, create_access_token


class UserService:

    @staticmethod
    def create_user(name: str, password: str) -> Result[None] | Result[UserRead]:
        user = UserMapper.find_by_name(name)
        if user:
            return Result.error(message="用户名已存在", code=400)
        new_user = UserMapper.create(name, password)
        return Result.success(data=new_user, message="用户创建成功")

    @staticmethod
    def update_user(user_id: int, name: str, password: str | None = None) -> Result[None] | Result[UserRead]:
        user = UserMapper.find_by_id(user_id)
        if not user:
            return Result.error(message="用户不存在", code=404)
        updated_user = UserMapper.update(user, name, password)
        return Result.success(data=updated_user, message="用户更新成功")

    @staticmethod
    def get_user_by_id(user_id: int) -> Result[None] | Result[UserRead]:
        user = UserMapper.find_by_id(user_id)
        if not user:
            return Result.error(message="用户不存在", code=404)
        return Result.success(data=user)

    @staticmethod
    def get_user_by_name(name: str) -> Result[None] | Result[UserRead]:
        user = UserMapper.find_by_name(name)
        if not user:
            return Result.error(message="用户不存在", code=404)
        return Result.success(data=user)
    @staticmethod
    def register(name: str, password: str) -> Result[None] | Result[UserRead]:
        user = UserMapper.find_by_name(name)
        if user:
            return Result.error(message="用户名已存在", code=400)
        hashed_pwd = hash_password(password)
        new_user = UserMapper.create(name, hashed_pwd)
        return Result.success(data=new_user, message="注册成功")

    @staticmethod
    def login(name: str, password: str) -> Result[None] | Result[UserRead]:
        user = UserMapper.find_by_name(name)
        if not user:
            return Result.error(message="用户不存在", code=404)
        # 校验密码
        if not verify_password(password, user.password):
            return Result.error(message="密码错误", code=401)
        # 生成 JWT
        token = create_access_token({"sub": str(user.id), "name": user.name})
        return Result.success(data=token, message="登录成功")