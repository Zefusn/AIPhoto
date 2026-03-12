from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Header
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import hashlib
import math
import pymysql
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from typing import Optional
from dotenv import load_dotenv
from qiniu import Auth, put_data, BucketManager
import io

# 加载环境变量
load_dotenv()

# 七牛云OSS配置
QINIU_ACCESS_KEY = os.getenv('QINIU_ACCESS_KEY', '')
QINIU_SECRET_KEY = os.getenv('QINIU_SECRET_KEY', '')
QINIU_BUCKET_NAME = os.getenv('QINIU_BUCKET_NAME', '')
QINIU_DOMAIN = os.getenv('QINIU_DOMAIN', '')  # 如: https://your-domain.com/

# 初始化七牛云
qiniu_auth = None
bucket_manager = None
if QINIU_ACCESS_KEY and QINIU_SECRET_KEY:
    qiniu_auth = Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)
    bucket_manager = BucketManager(qiniu_auth)

app = FastAPI()

# 配置CORS
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# MySQL数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '8.138.150.134'),
    'user': os.getenv('DB_USER', 'luckymax_login'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'luckymax_login'),
    'charset': os.getenv('DB_CHARSET', 'utf8mb4')
}

# 确保上传目录存在
UPLOAD_DIR = "uploads"
THUMBNAIL_DIR = "thumbnails"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

# 存储文件信息的字典
file_info = {}

# 存储会话 {token: username}
sessions = {}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)

def init_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 创建用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    nickname VARCHAR(64) DEFAULT '',
                    status TINYINT DEFAULT 1,
                    last_login_time DATETIME DEFAULT NULL,
                    last_login_ip VARCHAR(64) DEFAULT NULL,
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # 创建图片信息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    file_id VARCHAR(255) UNIQUE NOT NULL,
                    original_filename VARCHAR(500) NOT NULL,
                    display_name VARCHAR(500) DEFAULT '',
                    category VARCHAR(50) DEFAULT '电脑',
                    file_url TEXT NOT NULL,
                    thumbnail_url TEXT,
                    width INT DEFAULT 0,
                    height INT DEFAULT 0,
                    file_size BIGINT DEFAULT 0,
                    uploader VARCHAR(50) NOT NULL,
                    qiniu_key VARCHAR(500),
                    thumb_key VARCHAR(500),
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_category (category),
                    INDEX idx_uploader (uploader)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # 检查并创建管理员账户
            cursor.execute("SELECT username FROM users WHERE username = %s", ('admin',))
            if not cursor.fetchone():
                admin_password = hash_password('admin123')
                cursor.execute(
                    "INSERT INTO users (username, password, nickname, status) VALUES (%s, %s, %s, %s)",
                    ('admin', admin_password, '管理员', 1)
                )
                print("管理员账户已创建: admin / admin123")
            
            conn.commit()
    finally:
        conn.close()

def save_image_to_db(image_data: dict):
    """保存图片信息到数据库"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO images 
                (file_id, original_filename, display_name, category, file_url, thumbnail_url, 
                 width, height, file_size, uploader, qiniu_key, thumb_key)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                display_name = VALUES(display_name),
                category = VALUES(category),
                file_url = VALUES(file_url),
                thumbnail_url = VALUES(thumbnail_url),
                width = VALUES(width),
                height = VALUES(height),
                file_size = VALUES(file_size)
            """, (
                image_data['file_id'],
                image_data['original_filename'],
                image_data.get('display_name', ''),
                image_data.get('category', '电脑'),
                image_data.get('file_url', ''),
                image_data.get('thumbnail_url', ''),
                image_data.get('width', 0),
                image_data.get('height', 0),
                image_data.get('file_size', 0),
                image_data.get('uploader', ''),
                image_data.get('qiniu_key', ''),
                image_data.get('thumb_key', '')
            ))
            conn.commit()
    finally:
        conn.close()

def get_images_from_db():
    """从数据库获取所有图片信息"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT file_id, original_filename, display_name, category, file_url, 
                       thumbnail_url, width, height, file_size, uploader, qiniu_key, thumb_key
                FROM images ORDER BY create_time DESC
            """)
            rows = cursor.fetchall()
            result = {}
            for row in rows:
                result[row['file_id']] = {
                    'file_id': row['file_id'],
                    'original_filename': row['original_filename'],
                    'display_name': row['display_name'] or row['original_filename'],
                    'category': row['category'],
                    'file_url': row['file_url'],
                    'thumbnail_url': row['thumbnail_url'],
                    'width': row['width'],
                    'height': row['height'],
                    'file_size': row['file_size'],
                    'uploader': row['uploader'],
                    'qiniu_key': row['qiniu_key'],
                    'thumb_key': row['thumb_key']
                }
            return result
    finally:
        conn.close()

def delete_image_from_db(file_id: str):
    """从数据库删除图片信息"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM images WHERE file_id = %s", (file_id,))
            conn.commit()
    finally:
        conn.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(username: str) -> str:
    token = hashlib.sha256(f"{username}_{uuid.uuid4()}".encode()).hexdigest()
    sessions[token] = username
    return token

def verify_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    return sessions.get(token)

def upload_to_qiniu(file_data: bytes, key: str) -> str:
    """上传文件到七牛云OSS"""
    if not qiniu_auth or not QINIU_BUCKET_NAME:
        raise HTTPException(status_code=500, detail="七牛云未配置")
    
    # 生成上传凭证
    token = qiniu_auth.upload_token(QINIU_BUCKET_NAME, key, 3600)
    
    # 上传文件
    ret, info = put_data(token, key, file_data)
    
    if info.status_code == 200:
        # 返回基础URL（不带签名，访问时动态生成签名）
        if QINIU_DOMAIN:
            return f"{QINIU_DOMAIN.rstrip('/')}/{key}"
        else:
            return f"https://{QINIU_BUCKET_NAME}.qiniudn.com/{key}"
    else:
        raise HTTPException(status_code=500, detail=f"上传失败: {info}")

def get_private_url(base_url: str, expires: int = 3600) -> str:
    """生成私有空间的签名URL（有效期默认1小时）"""
    if not qiniu_auth:
        return base_url
    
    # 强制使用HTTP（避免测试域名SSL证书问题）
    if base_url.startswith('https://'):
        base_url = 'http://' + base_url[8:]
    
    # 七牛云私有URL生成
    return qiniu_auth.private_download_url(base_url, expires=expires)

def delete_from_qiniu(key: str):
    """从七牛云删除文件"""
    if not bucket_manager or not QINIU_BUCKET_NAME:
        return
    
    ret, info = bucket_manager.delete(QINIU_BUCKET_NAME, key)
    return info.status_code == 200

def get_user_from_db(username: str):
    try:
        # 尝试从数据库获取
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 检查用户是否存在
                cursor.execute("SELECT username, password, status FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                if user:
                    # 简单处理，admin用户默认为管理员
                    user["is_admin"] = username == "admin"
                return user
        finally:
            conn.close()
    except Exception as e:
        print(f"数据库查询错误: {e}")
        return None

def create_user(username: str, password_hash: str, is_admin: bool = False):
    try:
        # 尝试写入数据库
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (username, password, nickname, status) VALUES (%s, %s, %s, %s)",
                    (username, password_hash, username, 1)
                )
                conn.commit()
        finally:
            conn.close()
    except Exception as e:
        print(f"数据库写入错误: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        print("数据库连接成功")
        print("管理员账户已初始化到数据库")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        print("系统将拒绝登录请求，直到数据库连接恢复")

@app.post("/register")
async def register(username: str = Form(...), password: str = Form(...)):
    user = get_user_from_db(username)
    if user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    create_user(username, hash_password(password), False)
    
    return {"message": "注册成功", "username": username}

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...), x_forwarded_for: Optional[str] = Header(None)):
    user = get_user_from_db(username)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 检查用户状态
    if user.get("status") != 1:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    
    if user["password"] != hash_password(password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 更新登录信息
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 获取客户端IP
            client_ip = x_forwarded_for or "127.0.0.1"
            cursor.execute(
                "UPDATE users SET last_login_time = NOW(), last_login_ip = %s WHERE username = %s",
                (client_ip, username)
            )
            conn.commit()
    finally:
        conn.close()
    
    token = generate_token(username)
    
    return {
        "message": "登录成功",
        "token": token,
        "username": username,
        "is_admin": user["is_admin"]
    }

@app.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    username = verify_token(authorization)
    if username and authorization:
        token = authorization[7:]
        sessions.pop(token, None)
    return {"message": "退出登录成功"}

@app.get("/user")
async def get_user_info(authorization: Optional[str] = Header(None)):
    username = verify_token(authorization)
    if not username:
        return {"logged_in": False, "is_admin": False}
    
    user = get_user_from_db(username)
    
    return {
        "logged_in": True,
        "username": username,
        "is_admin": user["is_admin"] if user else False
    }

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    wallpaper_name: str = Form(None),
    category: str = Form('电脑'),
    authorization: Optional[str] = Header(None)
):
    username = verify_token(authorization)
    if not username:
        raise HTTPException(status_code=401, detail="请先登录")
    
    file_id = str(uuid.uuid4())
    original_filename = file.filename
    display_name = wallpaper_name if wallpaper_name else original_filename
    
    # 读取文件内容
    content = await file.read()
    file_size = len(content)
    
    # 处理图片获取尺寸
    img_width, img_height = 0, 0
    try:
        img = Image.open(io.BytesIO(content))
        img_width, img_height = img.size
    except Exception as e:
        print(f"获取图片尺寸失败: {e}")
    
    # 上传到七牛云（原图）
    file_key = f"images/{file_id}_{original_filename}"
    file_url = upload_to_qiniu(content, file_key)
    
    # 使用原图URL作为缩略图（七牛云会自动处理）
    # 这样避免生成缩略图的时间消耗
    thumbnail_url = file_url
    thumb_key = file_key
    
    file_info[file_id] = {
        "file_id": file_id,
        "original_filename": original_filename,
        "display_name": display_name,
        "category": category,
        "file_url": file_url,
        "thumbnail_url": thumbnail_url,
        "width": img_width,
        "height": img_height,
        "file_size": file_size,
        "uploader": username,
        "qiniu_key": file_key,
        "thumb_key": thumb_key
    }
    
    # 保存到数据库
    try:
        print(f"准备保存图片到数据库: file_id={file_id}, filename={original_filename}")
        save_image_to_db(file_info[file_id])
        print(f"图片信息已保存到数据库")
    except Exception as e:
        print(f"保存图片信息到数据库失败: {e}")
        import traceback
        traceback.print_exc()
    
    share_url = f"/download/{file_id}"
    return {"file_id": file_id, "share_url": share_url, "original_filename": original_filename, "display_name": display_name, "category": category, "url": file_url, "thumbnail_url": thumbnail_url}

@app.delete("/image/{file_id}")
async def delete_image(file_id: str, authorization: Optional[str] = Header(None)):
    username = verify_token(authorization)
    if not username:
        raise HTTPException(status_code=401, detail="请先登录")
    
    user = get_user_from_db(username)
    if not user or not user["is_admin"]:
        raise HTTPException(status_code=403, detail="权限不足，只有管理员可以删除图片")
    
    if file_id not in file_info:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    file_data = file_info[file_id]
    
    # 删除七牛云上的文件
    try:
        if file_data.get("qiniu_key"):
            delete_from_qiniu(file_data["qiniu_key"])
        if file_data.get("thumb_key"):
            delete_from_qiniu(file_data["thumb_key"])
    except Exception as e:
        print(f"删除七牛云文件失败: {e}")
    
    # 兼容本地文件删除（旧数据）
    try:
        if "file_path" in file_data and os.path.exists(file_data["file_path"]):
            os.remove(file_data["file_path"])
        if "thumbnail_path" in file_data and os.path.exists(file_data.get("thumbnail_path", "")):
            os.remove(file_data["thumbnail_path"])
    except Exception as e:
        print(f"删除本地文件失败: {e}")
    
    del file_info[file_id]
    
    # 从数据库删除
    try:
        delete_image_from_db(file_id)
    except Exception as e:
        print(f"从数据库删除图片信息失败: {e}")
    
    return {"message": "删除成功"}

@app.get("/download/{file_id}")
async def download_file(file_id: str, authorization: Optional[str] = Header(None)):
    if file_id not in file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    username = verify_token(authorization)
    if not username:
        raise HTTPException(status_code=401, detail="请先登录才能下载")
    
    file_data = file_info[file_id]
    
    # 如果有七牛云URL，生成签名URL并重定向
    if file_data.get("file_url"):
        signed_url = get_private_url(file_data["file_url"], expires=3600)
        return RedirectResponse(url=signed_url)
    
    # 兼容旧数据（本地文件）
    file_path = file_data.get("file_path")
    original_filename = file_data["original_filename"]
    
    if file_path and os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename=original_filename,
            media_type="application/octet-stream"
        )
    else:
        raise HTTPException(status_code=404, detail="文件不存在")

def format_file_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

@app.get("/images")
async def get_images(authorization: Optional[str] = Header(None)):
    username = verify_token(authorization)
    is_logged_in = username is not None
    
    print(f"/images 接口被调用，file_info 中有 {len(file_info)} 张图片")
    
    images = []
    for file_id, data in file_info.items():
        width = data.get("width", 0)
        height = data.get("height", 0)
        file_size = data.get("file_size", 0)
        resolution = f"{width}x{height}" if width > 0 and height > 0 else "未知"
        size_str = format_file_size(file_size) if file_size > 0 else "未知"
        
        # 优先使用七牛云URL，生成签名URL
        thumbnail_url = data.get("thumbnail_url")
        if thumbnail_url:
            thumbnail_url = get_private_url(thumbnail_url, expires=3600)
        elif data.get("thumbnail_path") and os.path.exists(data["thumbnail_path"]):
            thumbnail_url = f"/thumbnail/{file_id}"
        
        # 为七牛云文件URL生成签名
        file_url = data.get("file_url")
        if file_url:
            file_url = get_private_url(file_url, expires=3600)
        
        image_data = {
            "file_id": file_id,
            "original_filename": data["original_filename"],
            "display_name": data.get("display_name", data["original_filename"]),
            "category": data.get("category", "电脑"),
            "share_url": f"/download/{file_id}",
            "thumbnail_url": thumbnail_url,
            "file_url": file_url,
            "resolution": resolution,
            "size": size_str,
            "uploader": data.get("uploader", "未知")
        }
        
        images.append(image_data)
    
    return {"images": images, "logged_in": is_logged_in}

@app.get("/thumbnail/{file_id}")
async def get_thumbnail(file_id: str):
    if file_id not in file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_data = file_info[file_id]
    
    # 优先使用七牛云缩略图URL，生成签名URL
    if file_data.get("thumbnail_url"):
        signed_url = get_private_url(file_data["thumbnail_url"], expires=3600)
        return RedirectResponse(url=signed_url)
    
    # 兼容旧数据（本地文件）
    thumbnail_path = file_data.get("thumbnail_path")
    if thumbnail_path and os.path.exists(thumbnail_path):
        return FileResponse(
            path=thumbnail_path,
            media_type="image/jpeg"
        )
    
    raise HTTPException(status_code=404, detail="Thumbnail not found")

# 启动时从数据库加载图片信息
def load_images_from_db():
    """从数据库加载图片信息到内存"""
    global file_info
    try:
        file_info = get_images_from_db()
        print(f"从数据库加载了 {len(file_info)} 张图片")
    except Exception as e:
        print(f"从数据库加载图片信息失败: {e}")
        file_info = {}

# 使用FastAPI的startup事件加载数据
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    print("应用启动中...")
    # 初始化数据库
    try:
        init_db()
        print("数据库初始化完成")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
    
    # 加载图片数据
    load_images_from_db()
    print("应用启动完成")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('APP_PORT', '8003'))
    uvicorn.run(app, host="0.0.0.0", port=port)
