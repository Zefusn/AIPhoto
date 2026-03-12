import os
from dotenv import load_dotenv
import oss2

load_dotenv()

ALIYUN_ACCESS_KEY_ID = os.getenv('ALIYUN_ACCESS_KEY_ID')
ALIYUN_ACCESS_KEY_SECRET = os.getenv('ALIYUN_ACCESS_KEY_SECRET')
ALIYUN_BUCKET_NAME = os.getenv('ALIYUN_BUCKET_NAME')
ALIYUN_ENDPOINT = os.getenv('ALIYUN_ENDPOINT')
ALIYUN_CDN_DOMAIN = os.getenv('ALIYUN_CDN_DOMAIN')

bucket = None

if ALIYUN_ACCESS_KEY_ID and ALIYUN_ACCESS_KEY_SECRET:
    auth = oss2.Auth(ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET)
    bucket = oss2.Bucket(auth, ALIYUN_ENDPOINT, ALIYUN_BUCKET_NAME)

def upload_to_oss(file_data: bytes, key: str) -> str:
    """上传文件到阿里云OSS"""
    from fastapi import HTTPException
    
    if not bucket:
        raise HTTPException(status_code=500, detail="阿里云OSS未配置")
    
    try:
        bucket.put_object(key, file_data)
        if ALIYUN_CDN_DOMAIN:
            domain = ALIYUN_CDN_DOMAIN.rstrip('/')
            if not domain.startswith('https://'):
                domain = 'https://' + domain.lstrip('http://')
            return f"{domain}/{key}"
        else:
            return f"https://{ALIYUN_BUCKET_NAME}.{ALIYUN_ENDPOINT}/{key}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {e}")

def get_private_url(base_url: str, expires: int = 3600) -> str:
    """生成私有空间的签名URL（有效期默认1小时）"""
    # 移除URL中的查询参数
    base_url = base_url.split('?')[0]
    
    # 当bucket未初始化时，确保返回HTTPS URL
    if not bucket:
        if base_url.startswith('http://'):
            return base_url.replace('http://', 'https://')
        return base_url
    
    # 从URL中提取key
    key = None
    if ALIYUN_CDN_DOMAIN:
        # 规范化CDN域名，确保使用HTTPS
        cdn_domain = ALIYUN_CDN_DOMAIN.rstrip('/')
        if not cdn_domain.startswith('https://'):
            cdn_domain = 'https://' + cdn_domain.lstrip('http://')
        
        # 检查base_url是否以规范化的CDN域名开头
        if base_url.startswith(cdn_domain):
            key = base_url[len(cdn_domain):].lstrip('/')
            print(f"从CDN URL提取key: {key}")
    
    # 如果没有从CDN域名提取到key，尝试从OSS默认域名提取
    if not key and ALIYUN_ENDPOINT:
        if base_url.startswith(f"https://{ALIYUN_BUCKET_NAME}.{ALIYUN_ENDPOINT}"):
            key = base_url[len(f"https://{ALIYUN_BUCKET_NAME}.{ALIYUN_ENDPOINT}"):].lstrip('/')
            print(f"从OSS HTTPS URL提取key: {key}")
        elif base_url.startswith(f"http://{ALIYUN_BUCKET_NAME}.{ALIYUN_ENDPOINT}"):
            key = base_url[len(f"http://{ALIYUN_BUCKET_NAME}.{ALIYUN_ENDPOINT}"):].lstrip('/')
            print(f"从OSS HTTP URL提取key: {key}")
        else:
            # 直接使用key
            key = base_url
            print(f"直接使用key: {key}")
    
    # 如果成功提取key，生成签名URL
    if key:
        try:
            # 生成签名URL，添加Content-Disposition响应头
            headers = {
                'Content-Disposition': 'attachment'
            }
            signed_url = bucket.sign_url('GET', key, expires, headers=headers)
            print(f"生成的签名URL: {signed_url}")
            # 确保签名URL使用HTTPS协议
            if signed_url.startswith('http://'):
                signed_url = signed_url.replace('http://', 'https://')
                print(f"转换为HTTPS的签名URL: {signed_url}")
            # 如果配置了CDN域名，替换为CDN域名
            if ALIYUN_CDN_DOMAIN:
                cdn_domain = ALIYUN_CDN_DOMAIN.rstrip('/')
                if not cdn_domain.startswith('https://'):
                    cdn_domain = 'https://' + cdn_domain.lstrip('http://')
                # 从签名URL中提取查询参数
                if '?' in signed_url:
                    query_params = signed_url.split('?')[1]
                    cdn_url = f"{cdn_domain}/{key}?{query_params}"
                    print(f"生成的CDN签名URL: {cdn_url}")
                    return cdn_url
            print(f"最终返回的签名URL: {signed_url}")
            return signed_url
        except Exception as e:
            print(f"生成签名URL失败: {e}")
            # 失败时返回原始URL
            if base_url.startswith('http://'):
                return base_url.replace('http://', 'https://')
            return base_url
    else:
        # 如果不是阿里云OSS URL，确保返回HTTPS URL
        if base_url.startswith('http://'):
            return base_url.replace('http://', 'https://')
        return base_url

def delete_from_oss(key: str):
    """从阿里云OSS删除文件"""
    if not bucket:
        return
    
    try:
        bucket.delete_object(key)
        return True
    except:
        return False
