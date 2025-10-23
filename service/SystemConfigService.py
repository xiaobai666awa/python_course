from functools import lru_cache
from typing import Dict, Optional

from config import get_database_url, update_database_url
from mapper.SystemConfigMapper import SystemConfigMapper
from pojo.Result import Result


DATABASE_URL_KEY = "database_url"
HOJ_BASE_URL_KEY = "hoj_base_url"
HOJ_USERNAME_KEY = "hoj_username"
HOJ_PASSWORD_KEY = "hoj_password"


class SystemConfigService:
    SENSITIVE_KEYS = {HOJ_PASSWORD_KEY}

    @staticmethod
    def get_config(keys: Optional[list[str]] = None) -> Result[Dict[str, str]]:
        configs = SystemConfigMapper.get_many(keys) if keys else {
            item.key: item for item in SystemConfigMapper.all()
        }
        data = {key: value.value for key, value in configs.items()}

        # Always include current runtime values
        if keys is None or DATABASE_URL_KEY in keys:
            data[DATABASE_URL_KEY] = get_database_url()

        if HOJ_BASE_URL_KEY not in data:
            data[HOJ_BASE_URL_KEY] = SystemConfigService._get_env_default(HOJ_BASE_URL_KEY)
        if HOJ_USERNAME_KEY not in data:
            data[HOJ_USERNAME_KEY] = SystemConfigService._get_env_default(HOJ_USERNAME_KEY)

        if keys is None or HOJ_PASSWORD_KEY in keys:
            pwd = configs.get(HOJ_PASSWORD_KEY)
            data[HOJ_PASSWORD_KEY] = pwd.value if pwd else ""

        return Result.success(data=data, message="获取配置成功")

    @staticmethod
    def update_config(updates: Dict[str, str]) -> Result[Dict[str, str]]:
        response: Dict[str, str] = {}
        if DATABASE_URL_KEY in updates:
            new_url = updates[DATABASE_URL_KEY].strip()
            update_database_url(new_url)
            SystemConfigMapper.set(DATABASE_URL_KEY, new_url, description="数据库连接地址")
            response[DATABASE_URL_KEY] = new_url

        for key in (HOJ_BASE_URL_KEY, HOJ_USERNAME_KEY, HOJ_PASSWORD_KEY):
            if key in updates:
                value = updates[key].strip()
                SystemConfigMapper.set(key, value)
                if key in SystemConfigService.SENSITIVE_KEYS:
                    response[key] = "***"
                else:
                    response[key] = value

        SystemConfigService.get_hoj_settings.cache_clear()
        return Result.success(data=response, message="配置已更新")

    @staticmethod
    @lru_cache(maxsize=1)
    def get_hoj_settings() -> Dict[str, str]:
        configs = SystemConfigMapper.get_many(
            [HOJ_BASE_URL_KEY, HOJ_USERNAME_KEY, HOJ_PASSWORD_KEY]
        )

        base_url = (
            configs[HOJ_BASE_URL_KEY].value
            if configs.get(HOJ_BASE_URL_KEY)
            else SystemConfigService._get_env_default(HOJ_BASE_URL_KEY, default="https://127.0.0.1")
        )

        username = (
            configs[HOJ_USERNAME_KEY].value
            if configs.get(HOJ_USERNAME_KEY)
            else SystemConfigService._get_env_default(HOJ_USERNAME_KEY)
        )

        password = (
            configs[HOJ_PASSWORD_KEY].value
            if configs.get(HOJ_PASSWORD_KEY)
            else SystemConfigService._get_env_default(HOJ_PASSWORD_KEY)
        )

        return {
            "base_url": base_url,
            "username": username,
            "password": password,
        }

    @staticmethod
    def _get_env_default(key: str, default: str = "") -> str:
        env_key = key.upper()
        return SystemConfigService._env_value(env_key, default)

    @staticmethod
    def _env_value(key: str, default: str = "") -> str:
        return SystemConfigService._safe_strip(SystemConfigService._get_env(key, default))

    @staticmethod
    def _get_env(key: str, default: str = "") -> str:
        return SystemConfigService._os_environ().get(key, default)

    @staticmethod
    def _os_environ():
        import os

        return os.environ

    @staticmethod
    def _safe_strip(value: str) -> str:
        return value.strip() if isinstance(value, str) else value
