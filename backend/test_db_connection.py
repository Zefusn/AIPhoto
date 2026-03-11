import os
from dotenv import load_dotenv
import pymysql

# 加载环境变量
load_dotenv()

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '8.138.150.134'),
    'user': os.getenv('DB_USER', 'luckymax_login'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'luckymax_login'),
    'charset': os.getenv('DB_CHARSET', 'utf8mb4')
}

def test_db_connection():
    """测试数据库连接"""
    print("开始测试数据库连接...")
    print(f"连接信息: {DB_CONFIG['host']}:{DB_CONFIG['user']}@{DB_CONFIG['database']}")
    
    try:
        # 尝试连接数据库
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset=DB_CONFIG['charset'],
            connect_timeout=10
        )
        
        print("✅ 数据库连接成功!")
        
        # 测试查询
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"数据库版本: {version[0]}")
        
        conn.close()
        return True
        
    except pymysql.MySQLError as e:
        print(f"❌ 数据库连接失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

if __name__ == "__main__":
    test_db_connection()
