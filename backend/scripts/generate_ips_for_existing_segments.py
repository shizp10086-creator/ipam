"""
为已存在的网段生成 IP 地址记录
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.network_segment import NetworkSegment
from app.models.ip_address import IPAddress
import ipaddress


def generate_ips_for_segment(db, segment):
    """为指定网段生成 IP 地址"""
    cidr = f"{segment.network}/{segment.prefix_length}"
    print(f"Processing segment: {segment.name} ({cidr})")
    
    # 检查是否已有 IP 地址
    existing_count = db.query(IPAddress).filter(
        IPAddress.segment_id == segment.id
    ).count()
    
    if existing_count > 0:
        print(f"  Segment already has {existing_count} IP addresses, skipping...")
        return 0
    
    # 计算网段内的所有 IP 地址
    network = ipaddress.ip_network(cidr, strict=False)
    ip_addresses = []
    
    # 排除网络地址和广播地址
    for ip in network.hosts():
        ip_addr = IPAddress(
            segment_id=segment.id,
            ip_address=str(ip),
            status='available',
            is_online=False
        )
        ip_addresses.append(ip_addr)
    
    # 批量插入 IP 地址
    if ip_addresses:
        db.bulk_save_objects(ip_addresses)
        db.commit()
        print(f"  Created {len(ip_addresses)} IP addresses")
        return len(ip_addresses)
    
    return 0


def main():
    """主函数"""
    db = SessionLocal()
    
    try:
        # 获取所有网段
        segments = db.query(NetworkSegment).all()
        print(f"Found {len(segments)} segments")
        print("-" * 50)
        
        total_ips = 0
        for segment in segments:
            count = generate_ips_for_segment(db, segment)
            total_ips += count
        
        print("-" * 50)
        print(f"Total IP addresses created: {total_ips}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
