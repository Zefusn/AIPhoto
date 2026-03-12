import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '8.138.150.134'),
    'user': os.getenv('DB_USER', 'luckymax_login'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'luckymax_login'),
    'charset': os.getenv('DB_CHARSET', 'utf8mb4')
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)

def init_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
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
            
            cursor.execute("SELECT username FROM users WHERE username = %s", (os.getenv('ADMIN_USERNAME', 'admin'),))
            if not cursor.fetchone():
                import hashlib
                admin_password = hashlib.sha256(os.getenv('ADMIN_PASSWORD', 'admin123').encode()).hexdigest()
                cursor.execute(
                    "INSERT INTO users (username, password, nickname, status) VALUES (%s, %s, %s, %s)",
                    (os.getenv('ADMIN_USERNAME', 'admin'), admin_password, '管理员', 1)
                )
                print(f"管理员账户已创建: {os.getenv('ADMIN_USERNAME', 'admin')} / {os.getenv('ADMIN_PASSWORD', 'admin123')}")
            
            conn.commit()
    finally:
        conn.close()

def save_image_to_db(image_data: dict):
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
                    user["is_admin"] = username == os.getenv('ADMIN_USERNAME', 'admin')
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
