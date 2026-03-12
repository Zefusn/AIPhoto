import os
from dotenv import load_dotenv

load_dotenv()

from qiniu import Auth, BucketManager

QINIU_ACCESS_KEY = os.getenv('QINIU_ACCESS_KEY', '')
QINIU_SECRET_KEY = os.getenv('QINIU_SECRET_KEY', '')
QINIU_BUCKET_NAME = os.getenv('QINIU_BUCKET_NAME', '')
QINIU_DOMAIN = os.getenv('QINIU_DOMAIN', '')

qiniu_auth = None
bucket_manager = None

if QINIU_ACCESS_KEY and QINIU_SECRET_KEY:
    qiniu_auth = Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)
    bucket_manager = BucketManager(qiniu_auth)

def upload_to_qiniu(file_data: bytes, key: str) -> str:
    """上传文件到七牛云OSS"""
    from fastapi import HTTPException
    
    if not qiniu_auth or not QINIU_BUCKET_NAME:
        raise HTTPException(status_code=500, detail="七牛云未配置")
    
    from qiniu import put_data
    token = qiniu_auth.upload_token(QINIU_BUCKET_NAME, key, 3600)
    ret, info = put_data(token, key, file_data)
    
    if info.status_code == 200:
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
    
    if base_url.startswith('https://'):
        base_url = 'http://' + base_url[8:]
    
    return qiniu_auth.private_download_url(base_url, expires=expires)

def delete_from_qiniu(key: str):
    """从七牛云删除文件"""
    if not bucket_manager or not QINIU_BUCKET_NAME:
        return
    
    ret, info = bucket_manager.delete(QINIU_BUCKET_NAME, key)
    return info.status_code == 200
