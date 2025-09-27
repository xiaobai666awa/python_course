# 创建用户
import json
from datetime import datetime

from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from mapper.UserMapper import UserMapper
from pojo.User import UserCreate, UserUpdate

user_read=UserMapper.to_read()
print(json.dumps(user_read.model_dump(), indent=2, ensure_ascii=False,default=lambda d: d.strftime("%Y-%m-%d %H:%M:%S") if isinstance(d, datetime) else str(d)))

