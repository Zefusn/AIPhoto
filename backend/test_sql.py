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

def test_sql():
    """测试SQL执行"""
    print("开始测试SQL执行...")
    
    try:
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        print("✅ 数据库连接成功")
        
        with conn.cursor() as cursor:
            # 测试简单SQL
            print("测试简单SQL...")
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✅ 简单SQL执行成功: {result}")
            
            # 测试创建表
            print("测试创建表...")
            cursor.execute("DROP TABLE IF EXISTS test_table")
            cursor.execute("CREATE TABLE test_table (id INT PRIMARY KEY, name VARCHAR(255))")
            print("✅ 表创建成功")
            
            # 测试插入数据
            print("测试插入数据...")
            cursor.execute("INSERT INTO test_table VALUES (1, 'test')")
            conn.commit()
            print("✅ 数据插入成功")
            
            # 测试查询数据
            print("测试查询数据...")
            cursor.execute("SELECT * FROM test_table")
            result = cursor.fetchone()
            print(f"✅ 数据查询成功: {result}")
            
            # 清理测试表
            cursor.execute("DROP TABLE test_table")
            conn.commit()
            print("✅ 测试表清理成功")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    test_sql()
