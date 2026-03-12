from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException
from fastapi.responses import RedirectResponse
import os
import uuid
import io
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from database import save_image_to_db, delete_image_from_db, get_images_from_db, update_image_in_db
from utils import verify_token, format_file_size
from qiniu_ import upload_to_qiniu, get_private_url, delete_from_qiniu

router = APIRouter(prefix="", tags=["图片管理"])

file_info = {}

def load_images_from_db():
    global file_info
    try:
        file_info = get_images_from_db()
        print(f"从数据库加载了 {len(file_info)} 张图片")
    except Exception as e:
        print(f"从数据库加载图片信息失败: {e}")
        file_info = {}

def get_file_info():
    return file_info

@router.on_event("startup")
async def startup():
    load_images_from_db()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    wallpaper_name: str = Form(None),
    category: str = Form("电脑"),
    authorization: str = Header(None)
):
    username = verify_token(authorization)
    if not username:
        raise HTTPException(status_code=401, detail="请先登录")
    
    print(f"DEBUG: wallpaper_name = {wallpaper_name}")
    print(f"DEBUG: category = {category}")
    
    file_id = str(uuid.uuid4())
    original_filename = file.filename
    display_name = wallpaper_name if wallpaper_name else original_filename
    
    content = await file.read()
    file_size = len(content)
    
    img_width, img_height = 0, 0
    try:
        img = Image.open(io.BytesIO(content))
        img_width, img_height = img.size
    except Exception as e:
        print(f"获取图片尺寸失败: {e}")
    
    file_key = f"images/{file_id}_{original_filename}"
    file_url = upload_to_qiniu(content, file_key)
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
    
    try:
        save_image_to_db(file_info[file_id])
    except Exception as e:
        print(f"保存图片信息到数据库失败: {e}")
    
    share_url = f"/download/{file_id}"
    return {"file_id": file_id, "share_url": share_url, "original_filename": original_filename, "display_name": display_name, "category": category, "url": file_url, "thumbnail_url": thumbnail_url}

@router.delete("/image/{file_id}")
async def delete_image(file_id: str, authorization: str = Header(None)):
    username = verify_token(authorization)
    if not username:
        raise HTTPException(status_code=401, detail="请先登录")
    
    from database import get_user_from_db
    user = get_user_from_db(username)
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="权限不足，只有管理员可以删除图片")
    
    if file_id not in file_info:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    file_data = file_info[file_id]
    
    # 先从内存中删除，立即响应
    del file_info[file_id]
    
    # 异步执行耗时操作
    import asyncio
    
    async def cleanup_resources():
        # 删除七牛云原图和缩略图
        try:
            if file_data.get("qiniu_key"):
                delete_from_qiniu(file_data["qiniu_key"])
            if file_data.get("thumb_key"):
                delete_from_qiniu(file_data["thumb_key"])
        except Exception as e:
            print(f"删除七牛云文件失败: {e}")
        
        # 删除本地文件
        if "file_path" in file_data and os.path.exists(file_data.get("file_path", "")):
            try:
                os.remove(file_data["file_path"])
            except:
                pass
        
        # 从数据库删除
        try:
            delete_image_from_db(file_id)
        except Exception as e:
            print(f"从数据库删除图片信息失败: {e}")
    
    # 后台执行清理操作
    asyncio.create_task(cleanup_resources())
    
    return {"message": "删除成功"}

@router.put("/image/{file_id}")
async def update_image(
    file_id: str,
    display_name: str = None,
    category: str = None,
    authorization: str = Header(None)
):
    username = verify_token(authorization)
    if not username:
        raise HTTPException(status_code=401, detail="请先登录")
    
    from database import get_user_from_db
    user = get_user_from_db(username)
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="权限不足，只有管理员可以修改图片信息")
    
    if file_id not in file_info:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    file_info[file_id]["display_name"] = display_name if display_name else file_info[file_id].get("display_name", "")
    if category:
        file_info[file_id]["category"] = category
    
    try:
        update_image_in_db(file_id, display_name=display_name, category=category)
    except Exception as e:
        print(f"更新数据库失败: {e}")
    
    return {"message": "更新成功", "display_name": file_info[file_id]["display_name"], "category": file_info[file_id].get("category")}

@router.get("/download/{file_id}")
async def download_file(file_id: str, authorization: str = Header(None)):
    if file_id not in file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    username = verify_token(authorization)
    if not username:
        raise HTTPException(status_code=401, detail="请先登录才能下载")
    
    file_data = file_info[file_id]
    
    if file_data.get("file_url"):
        signed_url = get_private_url(file_data["file_url"], expires=3600)
        return RedirectResponse(url=signed_url)
    
    file_path = file_data.get("file_path")
    original_filename = file_data["original_filename"]
    
    if file_path and os.path.exists(file_path):
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            filename=original_filename,
            media_type="application/octet-stream"
        )
    else:
        raise HTTPException(status_code=404, detail="文件不存在")

@router.get("/images")
async def get_images(authorization: str = Header(None)):
    username = verify_token(authorization)
    is_logged_in = username is not None
    
    images = []
    for file_id, data in file_info.items():
        width = data.get("width", 0)
        height = data.get("height", 0)
        file_size = data.get("file_size", 0)
        resolution = f"{width}x{height}" if width > 0 and height > 0 else "未知"
        size_str = format_file_size(file_size) if file_size > 0 else "未知"
        
        # 直接返回原始URL，不在这里生成签名URL
        # 签名URL由前端在需要时生成，减少服务器压力
        image_data = {
            "file_id": file_id,
            "original_filename": data["original_filename"],
            "display_name": data.get("display_name", data["original_filename"]),
            "category": data.get("category", "电脑"),
            "share_url": f"/download/{file_id}",
            "thumbnail_url": data.get("thumbnail_url"),
            "file_url": data.get("file_url"),
            "resolution": resolution,
            "size": size_str,
            "uploader": data.get("uploader", "未知")
        }
        
        images.append(image_data)
    
    return {"images": images, "logged_in": is_logged_in}

@router.get("/thumbnail/{file_id}")
async def get_thumbnail(file_id: str):
    if file_id not in file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_data = file_info[file_id]
    
    thumbnail_url = file_data.get("thumbnail_url")
    if thumbnail_url:
        signed_url = get_private_url(thumbnail_url, expires=3600)
        return RedirectResponse(url=signed_url)
    
    thumbnail_path = file_data.get("thumbnail_path")
    if thumbnail_path and os.path.exists(thumbnail_path):
        from fastapi.responses import FileResponse
        return FileResponse(
            path=thumbnail_path,
            media_type="image/jpeg"
        )
    
    raise HTTPException(status_code=404, detail="缩略图不存在")
