from fastapi import APIRouter, Form, Header, HTTPException
from database import get_user_from_db, create_user, update_user_login_time
from utils import hash_password, generate_token, verify_token, remove_session

router = APIRouter(prefix="", tags=["用户认证"])

@router.post("/register")
async def register(username: str = Form(...), password: str = Form(...)):
    user = get_user_from_db(username)
    if user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    create_user(username, hash_password(password), False)
    return {"message": "注册成功", "username": username}

@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...), x_forwarded_for: str = Header(None)):
    user = get_user_from_db(username)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if user.get("status") != 1:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    
    if user["password"] != hash_password(password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    client_ip = x_forwarded_for or "127.0.0.1"
    try:
        update_user_login_time(username, client_ip)
    except:
        pass
    
    token = generate_token(username)
    
    return {
        "message": "登录成功",
        "token": token,
        "username": username,
        "is_admin": user["is_admin"]
    }

@router.post("/logout")
async def logout(authorization: str = Header(None)):
    username = verify_token(authorization)
    if username and authorization:
        token = authorization[7:]
        remove_session(token)
    return {"message": "退出登录成功"}

@router.get("/user")
async def get_user_info(authorization: str = Header(None)):
    username = verify_token(authorization)
    if not username:
        return {"logged_in": False, "is_admin": False}
    
    user = get_user_from_db(username)
    
    return {
        "logged_in": True,
        "username": username,
        "is_admin": user["is_admin"] if user else False
    }
