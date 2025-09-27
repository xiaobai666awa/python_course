from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from service.UserService import UserService
from utils.security import decode_access_token
from pojo.Result import Result

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")  # 登录接口路径

# ---------------- 注册 ----------------
@router.post("/register")
def register(name: str, password: str) -> Result:
    return UserService.register(name, password)


# ---------------- 登录 ----------------
@router.post("/login")
def login(name: str, password: str) -> Result:
    return UserService.login(name, password)


# ---------------- Token 验证依赖 ----------------
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
    return payload


# ---------------- 需要登录的接口示例 ----------------
@router.get("/me")
def get_me(current_user=Depends(get_current_user)) -> Result:
    return Result.success(data=current_user, message="当前用户信息")
