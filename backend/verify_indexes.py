"""
数据库索引验证脚本

此脚本用于验证 IPAM 系统数据库中的所有索引是否正确创建。
运行此脚本需要数据库已经初始化（运行过 Alembic 迁移）。

使用方法:
    python verify_indexes.py
"""

import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 期望的索引配置
EXPECTED_INDEXES = {
    "users": [
        {"column": "id", "unique": True, "description": "主键索引"},
        {"column": "username", "unique": True, "description": "用户名唯一索引"},
        {"column": "role", "unique": False, "description": "角色索引"},
    ],
    "network_segments": [
        {"column": "id", "unique": True, "description": "主键索引"},
        {"column": "network", "unique": False, "description": "网络地址索引"},
        {"column": "prefix_length", "unique": False, "description": "前缀长度索引"},
    ],
    "ip_addresses": [
        {"column": "id", "unique": True, "description": "主键索引"},
        {"column": "ip_address", "unique": True, "description": "IP 地址唯一索引"},
        {"column": "status", "unique": False, "description": "状态索引"},
        {"column": "segment_id", "unique": False, "description": "网段外键索引"},
        {"column": "device_id", "unique": False, "description": "设备外键索引"},
    ],
    "devices": [
        {"column": "id", "unique": True, "description": "主键索引"},
        {"column": "name", "unique": False, "description": "设备名称索引"},
        {"column": "mac_address", "unique": True, "description": "MAC 地址唯一索引"},
        {"column": "owner", "unique": False, "description": "责任人索引"},
    ],
    "operation_logs": [
        {"column": "id", "unique": True, "description": "主键索引"},
        {"column": "user_id", "unique": False, "description": "用户外键索引"},
        {"column": "operation_type", "unique": False, "description": "操作类型索引"},
        {"column": "resource_type", "unique": False, "description": "资源类型索引"},
        {"column": "created_at", "unique": False, "description": "创建时间索引"},
    ],
    "alerts": [
        {"column": "id", "unique": True, "description": "主键索引"},
        {"column": "segment_id", "unique": False, "description": "网段外键索引"},
        {"column": "is_resolved", "unique": False, "description": "解决状态索引"},
        {"column": "created_at", "unique": False, "description": "创建时间索引"},
    ],
}


def verify_indexes():
    """验证数据库索引"""
    print("=" * 80)
    print("IPAM 系统数据库索引验证")
    print("=" * 80)
    print()

    try:
        # 创建数据库连接
        engine = create_engine(settings.DATABASE_URL)
        inspector = inspect(engine)
        
        # 获取所有表名
        tables = inspector.get_table_names()
        print(f"✓ 成功连接到数据库")
        print(f"✓ 找到 {len(tables)} 个表: {', '.join(tables)}")
        print()
        
        all_passed = True
        total_indexes = 0
        
        # 验证每个表的索引
        for table_name, expected_indexes in EXPECTED_INDEXES.items():
            print(f"检查表: {table_name}")
            print("-" * 80)
            
            if table_name not in tables:
                print(f"  ✗ 错误: 表 '{table_name}' 不存在")
                all_passed = False
                print()
                continue
            
            # 获取表的实际索引
            actual_indexes = inspector.get_indexes(table_name)
            pk_constraint = inspector.get_pk_constraint(table_name)
            unique_constraints = inspector.get_unique_constraints(table_name)
            
            # 构建实际索引映射（包括主键和唯一约束）
            actual_index_map = {}
            
            # 添加主键
            if pk_constraint and 'constrained_columns' in pk_constraint:
                for col in pk_constraint['constrained_columns']:
                    actual_index_map[col] = {"unique": True, "type": "PRIMARY KEY"}
            
            # 添加唯一约束
            for constraint in unique_constraints:
                for col in constraint['column_names']:
                    actual_index_map[col] = {"unique": True, "type": "UNIQUE"}
            
            # 添加普通索引
            for index in actual_indexes:
                for col in index['column_names']:
                    if col not in actual_index_map:
                        actual_index_map[col] = {
                            "unique": index.get('unique', False),
                            "type": "INDEX"
                        }
            
            # 验证每个期望的索引
            table_passed = True
            for expected in expected_indexes:
                col = expected['column']
                expected_unique = expected['unique']
                description = expected['description']
                
                if col in actual_index_map:
                    actual = actual_index_map[col]
                    actual_unique = actual['unique']
                    index_type = actual['type']
                    
                    if expected_unique == actual_unique:
                        status = "✓"
                        total_indexes += 1
                    else:
                        status = "✗"
                        table_passed = False
                        all_passed = False
                    
                    unique_str = "UNIQUE" if actual_unique else "INDEX"
                    print(f"  {status} {col:20} [{unique_str:10}] - {description}")
                else:
                    print(f"  ✗ {col:20} [缺失] - {description}")
                    table_passed = False
                    all_passed = False
            
            if table_passed:
                print(f"  ✓ 表 '{table_name}' 的所有索引验证通过")
            else:
                print(f"  ✗ 表 '{table_name}' 的索引验证失败")
            
            print()
        
        # 打印总结
        print("=" * 80)
        if all_passed:
            print(f"✓ 验证通过！所有 {total_indexes} 个索引都已正确创建。")
            print()
            print("索引实现总结:")
            print("  - 用户表 (users): 3 个索引")
            print("  - 网段表 (network_segments): 3 个索引")
            print("  - IP 地址表 (ip_addresses): 5 个索引")
            print("  - 设备表 (devices): 4 个索引")
            print("  - 操作日志表 (operation_logs): 5 个索引")
            print("  - 告警表 (alerts): 4 个索引")
            print()
            print("所有索引符合设计文档要求（需求 16.4）。")
            return 0
        else:
            print("✗ 验证失败！部分索引缺失或配置不正确。")
            print()
            print("请检查:")
            print("  1. 数据库迁移是否已正确执行")
            print("  2. SQLAlchemy 模型定义是否正确")
            print("  3. 数据库连接是否正常")
            return 1
            
    except Exception as e:
        print(f"✗ 验证过程中发生错误: {str(e)}")
        print()
        print("可能的原因:")
        print("  1. 数据库未启动或连接失败")
        print("  2. 数据库迁移未执行")
        print("  3. 配置文件错误")
        return 1


def show_all_indexes():
    """显示数据库中的所有索引（详细信息）"""
    print()
    print("=" * 80)
    print("数据库索引详细信息")
    print("=" * 80)
    print()
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        inspector = inspect(engine)
        
        for table_name in EXPECTED_INDEXES.keys():
            print(f"表: {table_name}")
            print("-" * 80)
            
            # 主键
            pk = inspector.get_pk_constraint(table_name)
            if pk and 'constrained_columns' in pk:
                print(f"  主键: {', '.join(pk['constrained_columns'])}")
            
            # 唯一约束
            unique_constraints = inspector.get_unique_constraints(table_name)
            if unique_constraints:
                print("  唯一约束:")
                for constraint in unique_constraints:
                    cols = ', '.join(constraint['column_names'])
                    name = constraint.get('name', 'unnamed')
                    print(f"    - {name}: {cols}")
            
            # 索引
            indexes = inspector.get_indexes(table_name)
            if indexes:
                print("  索引:")
                for index in indexes:
                    cols = ', '.join(index['column_names'])
                    name = index.get('name', 'unnamed')
                    unique = " (UNIQUE)" if index.get('unique', False) else ""
                    print(f"    - {name}: {cols}{unique}")
            
            print()
            
    except Exception as e:
        print(f"✗ 获取索引信息时发生错误: {str(e)}")


if __name__ == "__main__":
    # 运行验证
    exit_code = verify_indexes()
    
    # 如果验证通过，显示详细信息
    if exit_code == 0:
        show_all_indexes()
    
    sys.exit(exit_code)
