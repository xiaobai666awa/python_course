import csv
import io
import os
from typing import Dict, List

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
    def ensure_admin_user() -> None:
        """
        确保系统中存在 admin 账户，如果缺失则初始化一个默认管理员。
        """
        admin_name = os.getenv("ADMIN_DEFAULT_NAME", "admin")
        admin_password = os.getenv("ADMIN_DEFAULT_PASSWORD", "admin123")

        if not admin_name or not admin_password:
            return

        if UserMapper.find_by_name(admin_name):
            return

        hashed_pwd = hash_password(admin_password)
        UserMapper.create(admin_name, hashed_pwd)
        print(f"[init] 已创建默认管理员账户: {admin_name}")

    @staticmethod
    def import_users_from_csv(file_bytes: bytes) -> Result[None] | Result[list[UserRead]]:
        """
        批量导入用户
        file_bytes: CSV 文件字节流, 必须包含 name,password 两列
        """
        try:
            if not file_bytes:
                return Result.error(message="上传文件为空")

            if len(file_bytes) > MAX_CSV_BYTES:
                return Result.error(message="CSV 文件过大，请分批导入")

            try:
                file_content = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return Result.error(message="CSV 文件必须为 UTF-8 编码")

            csv_reader = csv.DictReader(io.StringIO(file_content))

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
        except csv.Error as exc:
            return Result.error(message=f"CSV 解析失败: {str(exc)}")
        except Exception as e:
            return Result.error(message=f"导入失败: {str(e)}")
