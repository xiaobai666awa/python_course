import csv

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from starlette import status

from pojo.User import UserRead
from service.UserService import UserService
from utils.security import decode_access_token
from pojo.Result import Result

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")  # 登录接口路径
class RegisterRequest(BaseModel):
    name: str
    password: str

# ---------------- 注册 ----------------
@router.post("/register")
def register(req: RegisterRequest) -> Result:
    return UserService.register(req.name, req.password)



# ---------------- 登录 ----------------
@router.post("/login")
def login(req: RegisterRequest) -> Result:
    return UserService.login(req.name, req.password)


# ---------------- Token 验证依赖 ----------------
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
    return payload
def admin_required(current_user: dict = Depends(get_current_user)):
    """
    仅允许 admin 用户访问
    current_user 从 get_current_user 获取
    """
    if current_user.get("name") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有 admin 可以访问此接口"
        )
    return current_user

# ---------------- 需要登录的接口示例 ----------------
@router.get("/me")
def get_me(current_user=Depends(get_current_user)) -> Result:
    return Result.success(data=current_user, message="当前用户信息")


@router.post("/import")
async def import_users(file: UploadFile= File(...), _: dict = Depends(admin_required)):
    """批量导入用户（仅限 admin）"""
    try:
        # 调用 service 方法，传入文件流
        result: Result[list[UserRead]] = UserService.import_users_from_csv(file.file.read())
        return result
    except Exception as e:
        # 捕获 service 之外的异常
        return Result.error(message=f"导入失败: {str(e)}")