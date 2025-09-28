import csv
from io import StringIO
from typing import Any, IO, List

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
        return Result.success(data=UserMapper.to_read(user))

    @staticmethod
    def get_user_by_name(name: str) -> Result[None] | Result[UserRead]:
        user = UserMapper.find_by_name(name)
        if not user:
            return Result.error(message="用户不存在", code=404)
        return Result.success(data=UserMapper.to_read(user))
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
    @staticmethod
    def import_users_from_csv(file: IO) -> Result[None] | Result[list[UserRead]]:
        """
        批量导入用户
        file: CSV 文件流, 必须包含 name,password 两列
        """
        try:
            # 解析 CSV 文件
            file_content = file.read().decode("utf-8") if isinstance(file.read(), bytes) else file.read()
            csv_reader = csv.DictReader(StringIO(file_content))
            users_to_add = []
            for row in csv_reader:
                if "name" in row and "password" in row:
                    users_to_add.append({
                        "name": row["name"].strip(),
                        "password": row["password"].strip()
                    })

            if not users_to_add:
                return Result.error(message="CSV 文件中未找到有效用户数据")

            # 批量插入
            inserted_users = UserMapper.bulk_insert(users_to_add)

            # 返回 Result
            return Result.success(data=[UserRead.model_validate(u) for u in inserted_users],
                                  message=f"成功导入 {len(inserted_users)} 个用户")
        except Exception as e:
            return Result.error(message=f"导入失败: {str(e)}")