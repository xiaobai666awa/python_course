import csv
import io
import os
from typing import Dict, IO, List

from mapper.UserMapper import UserMapper
from pojo.User import User, UserRead
from pojo.Result import Result
from utils.security import hash_password, verify_password, create_access_token


MAX_CSV_BYTES = int(os.getenv("USER_IMPORT_MAX_BYTES", str(1024 * 1024)))  # 默认 1MB
MAX_CSV_ROWS = int(os.getenv("USER_IMPORT_MAX_ROWS", "1000"))


class UserService:

    @staticmethod
    def create_user(name: str, password: str) -> Result[None] | Result[UserRead]:
        user = UserMapper.find_by_name(name)
        if user:
            return Result.error(message="用户名已存在", code=400)
        hashed_pwd = hash_password(password)
        new_user = UserMapper.create(name, hashed_pwd)
        return Result.success(data=new_user, message="用户创建成功")

    @staticmethod
    def update_user(user_id: int, name: str, password: str | None = None) -> Result[None] | Result[UserRead]:
        user = UserMapper.find_by_id(user_id)
        if not user:
            return Result.error(message="用户不存在", code=404)
        hashed_pwd = hash_password(password) if password else None
        updated_user = UserMapper.update(user, name, hashed_pwd)
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
        token = create_access_token({"sub": str(user.id), "name": user.name,"user_id": user.id})
        return Result.success(data=token, message="登录成功")
    @staticmethod
    def import_users_from_csv(file_obj: IO[bytes]) -> Result[None] | Result[list[UserRead]]:
        """
        批量导入用户
        file_obj: CSV 文件流, 必须包含 name,password 两列
        """
        try:
            if hasattr(file_obj, "seek") and hasattr(file_obj, "tell"):
                try:
                    file_obj.seek(0, os.SEEK_END)
                    size = file_obj.tell()
                    if size > MAX_CSV_BYTES:
                        return Result.error(message="CSV 文件过大，请分批导入")
                    file_obj.seek(0)
                except OSError:
                    file_obj.seek(0)

            text_stream = io.TextIOWrapper(file_obj, encoding="utf-8", newline="")
            try:
                csv_reader = csv.DictReader(text_stream)

                users_to_add: List[Dict[str, str]] = []
                seen_names: set[str] = set()

                for index, row in enumerate(csv_reader, start=1):
                    if index > MAX_CSV_ROWS:
                        return Result.error(message="CSV 行数超出限制，请分批导入")

                    name = (row.get("name") or "").strip()
                    password = (row.get("password") or "").strip()

                    if not name or not password:
                        continue

                    if name in seen_names:
                        continue

                    seen_names.add(name)
                    users_to_add.append({
                        "name": name,
                        "password": hash_password(password)
                    })

                if not users_to_add:
                    return Result.error(message="CSV 文件中未找到有效用户数据")

                inserted_users = UserMapper.bulk_insert(users_to_add)

                return Result.success(
                    data=[UserRead.model_validate(u) for u in inserted_users],
                    message=f"成功导入 {len(inserted_users)} 个用户"
                )
            finally:
                text_stream.detach()
        except UnicodeDecodeError:
            return Result.error(message="CSV 文件必须为 UTF-8 编码")
        except csv.Error as exc:
            return Result.error(message=f"CSV 解析失败: {str(exc)}")
        except Exception as e:
            return Result.error(message=f"导入失败: {str(e)}")
