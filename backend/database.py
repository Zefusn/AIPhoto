import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': os.getenv('DB_CHARSET')
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)

def init_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 创建users表
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
            print("创建users表成功")
            
            # 删除旧的images表
            try:
                cursor.execute("DROP TABLE IF EXISTS images")
                print("删除旧images表成功")
            except Exception as e:
                print(f"删除旧images表失败: {e}")
            
            # 创建新的images表
            try:
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
                        oss_key VARCHAR(500),
                        thumb_oss_key VARCHAR(500),
                        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_category (category),
                        INDEX idx_uploader (uploader)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                print("创建新images表成功")
            except Exception as e:
                print(f"创建新images表失败: {e}")
            
            # 创建管理员账户
            cursor.execute("SELECT username FROM users WHERE username = %s", (os.getenv('ADMIN_USERNAME'),))
            if not cursor.fetchone():
                import hashlib
                admin_password = hashlib.sha256(os.getenv('ADMIN_PASSWORD').encode()).hexdigest()
                cursor.execute(
                    "INSERT INTO users (username, password, nickname, status) VALUES (%s, %s, %s, %s)",
                    (os.getenv('ADMIN_USERNAME'), admin_password, '管理员', 1)
                )
                print(f"管理员账户已创建: {os.getenv('ADMIN_USERNAME')} / {os.getenv('ADMIN_PASSWORD')}")
            
            conn.commit()
            print("数据库初始化完成")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        conn.rollback()
    finally:
        conn.close()

def save_image_to_db(image_data: dict):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO images 
                (file_id, original_filename, display_name, category, file_url, thumbnail_url, 
                 width, height, file_size, uploader, oss_key, thumb_oss_key)
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
                image_data.get('oss_key', ''),
                image_data.get('thumb_oss_key', '')
            ))
            conn.commit()
    finally:
        conn.close()

def get_images_from_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT file_id, original_filename, display_name, category, file_url, 
                       thumbnail_url, width, height, file_size, uploader, oss_key, thumb_oss_key
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
                    'oss_key': row['oss_key'],
                    'thumb_oss_key': row['thumb_oss_key']
                }
            return result
    finally:
        conn.close()

def delete_image_from_db(file_id: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM images WHERE file_id = %s", (file_id,))
            conn.commit()
    finally:
        conn.close()

def update_image_in_db(file_id: str, display_name: str = None, category: str = None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if display_name is not None:
                cursor.execute(
                    "UPDATE images SET display_name = %s WHERE file_id = %s",
                    (display_name, file_id)
                )
            if category is not None:
                cursor.execute(
                    "UPDATE images SET category = %s WHERE file_id = %s",
                    (category, file_id)
                )
            conn.commit()
    finally:
        conn.close()

def get_user_from_db(username: str):
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT username, password, status FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                if user:
                    user["is_admin"] = username == os.getenv('ADMIN_USERNAME')
                return user
        finally:
            conn.close()
    except Exception as e:
        print(f"数据库查询错误: {e}")
        return None

def create_user(username: str, password_hash: str, is_admin: bool = False):
    try:
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

def update_user_login_time(username: str, client_ip: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET last_login_time = NOW(), last_login_ip = %s WHERE username = %s",
                (client_ip, username)
            )
            conn.commit()
    finally:
        conn.close()
