from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from database import init_db
from routes.auth import router as auth_router
from routes.images import router as images_router

app = FastAPI(title="Luckymax API")

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

app.include_router(auth_router)
app.include_router(images_router)

@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        print("数据库连接成功")
        print("管理员账户已初始化到数据库")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        print("系统将拒绝登录请求，直到数据库连接恢复")

@app.get("/")
async def root():
    return {"message": "Luckymax API"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
