"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create all tables for the IPAM system
    """
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False, comment='用户名'),
        sa.Column('hashed_password', sa.String(length=255), nullable=False, comment='加密密码'),
        sa.Column('email', sa.String(length=100), nullable=False, comment='邮箱'),
        sa.Column('full_name', sa.String(length=100), nullable=False, comment='全名'),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='user', comment='角色: admin/user/readonly'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1', comment='是否激活'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'])
    
    # Create network_segments table
    op.create_table(
        'network_segments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='网段名称'),
        sa.Column('network', sa.String(length=45), nullable=False, comment='网络地址 (如 192.168.1.0)'),
        sa.Column('prefix_length', sa.Integer(), nullable=False, comment='前缀长度 (如 24)'),
        sa.Column('gateway', sa.String(length=45), nullable=True, comment='网关地址'),
        sa.Column('description', sa.Text(), nullable=True, comment='描述'),
        sa.Column('usage_threshold', sa.Integer(), nullable=False, server_default='80', comment='使用率告警阈值（百分比）'),
        sa.Column('created_by', sa.Integer(), nullable=False, comment='创建人 ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('ix_network_segments_id', 'network_segments', ['id'])
    op.create_index('ix_network_segments_network', 'network_segments', ['network', 'prefix_length'])
    
    # Create devices table
    op.create_table(
        'devices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='设备名称'),
        sa.Column('mac_address', sa.String(length=17), nullable=False, comment='MAC 地址'),
        sa.Column('device_type', sa.String(length=50), nullable=True, comment='设备类型（服务器/交换机/路由器/终端等）'),
        sa.Column('manufacturer', sa.String(length=100), nullable=True, comment='制造商'),
        sa.Column('model', sa.String(length=100), nullable=True, comment='型号'),
        sa.Column('owner', sa.String(length=100), nullable=False, comment='责任人'),
        sa.Column('department', sa.String(length=100), nullable=True, comment='部门'),
        sa.Column('location', sa.String(length=200), nullable=True, comment='物理位置'),
        sa.Column('description', sa.Text(), nullable=True, comment='描述'),
        sa.Column('created_by', sa.Integer(), nullable=False, comment='创建人 ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('ix_devices_id', 'devices', ['id'])
    op.create_index('ix_devices_mac_address', 'devices', ['mac_address'], unique=True)
    op.create_index('ix_devices_name', 'devices', ['name'])
    op.create_index('ix_devices_owner', 'devices', ['owner'])
    
    # Create ip_addresses table
    op.create_table(
        'ip_addresses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False, comment='IP 地址'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='available', comment='状态: available/used/reserved'),
        sa.Column('segment_id', sa.Integer(), nullable=False, comment='所属网段 ID'),
        sa.Column('device_id', sa.Integer(), nullable=True, comment='关联设备 ID'),
        sa.Column('allocated_by', sa.Integer(), nullable=True, comment='分配人 ID'),
        sa.Column('allocated_at', sa.DateTime(), nullable=True, comment='分配时间'),
        sa.Column('last_seen', sa.DateTime(), nullable=True, comment='最后扫描时间'),
        sa.Column('is_online', sa.Boolean(), nullable=False, server_default='0', comment='是否在线（最后扫描结果）'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['segment_id'], ['network_segments.id'], ),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.ForeignKeyConstraint(['allocated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('ix_ip_addresses_id', 'ip_addresses', ['id'])
    op.create_index('ix_ip_addresses_ip_address', 'ip_addresses', ['ip_address'], unique=True)
    op.create_index('ix_ip_addresses_segment_id', 'ip_addresses', ['segment_id'])
    op.create_index('ix_ip_addresses_status', 'ip_addresses', ['status'])
    op.create_index('ix_ip_addresses_device_id', 'ip_addresses', ['device_id'])
    
    # Create operation_logs table
    op.create_table(
        'operation_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='操作人 ID'),
        sa.Column('username', sa.String(length=50), nullable=False, comment='操作人用户名（冗余字段）'),
        sa.Column('operation_type', sa.String(length=20), nullable=False, comment='操作类型: create/update/delete/allocate/release'),
        sa.Column('resource_type', sa.String(length=20), nullable=False, comment='资源类型: ip/device/segment/user'),
        sa.Column('resource_id', sa.Integer(), nullable=True, comment='资源 ID'),
        sa.Column('details', sa.Text(), nullable=True, comment='操作详情（JSON 格式）'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='客户端 IP'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='操作时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('ix_operation_logs_id', 'operation_logs', ['id'])
    op.create_index('ix_operation_logs_user_id', 'operation_logs', ['user_id'])
    op.create_index('ix_operation_logs_operation_type', 'operation_logs', ['operation_type', 'resource_type'])
    op.create_index('ix_operation_logs_created_at', 'operation_logs', ['created_at'])
    
    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('segment_id', sa.Integer(), nullable=False, comment='网段 ID'),
        sa.Column('alert_type', sa.String(length=50), nullable=False, comment='告警类型: usage_threshold'),
        sa.Column('severity', sa.String(length=20), nullable=False, comment='严重程度: warning/critical'),
        sa.Column('message', sa.Text(), nullable=False, comment='告警消息'),
        sa.Column('current_usage', sa.Float(), nullable=False, comment='当前使用率'),
        sa.Column('threshold', sa.Float(), nullable=False, comment='阈值'),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='0', comment='是否已解决'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True, comment='解决时间'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='创建时间'),
        sa.ForeignKeyConstraint(['segment_id'], ['network_segments.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('ix_alerts_id', 'alerts', ['id'])
    op.create_index('ix_alerts_segment_id', 'alerts', ['segment_id'])
    op.create_index('ix_alerts_is_resolved', 'alerts', ['is_resolved'])
    op.create_index('ix_alerts_created_at', 'alerts', ['created_at'])
    
    # Create scan_history table
    op.create_table(
        'scan_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('segment_id', sa.Integer(), nullable=False, comment='网段 ID'),
        sa.Column('created_by', sa.Integer(), nullable=False, comment='发起人 ID'),
        sa.Column('scan_type', sa.String(length=20), nullable=False, comment='扫描类型: ping/arp'),
        sa.Column('total_ips', sa.Integer(), nullable=False, comment='扫描 IP 总数'),
        sa.Column('online_ips', sa.Integer(), nullable=False, comment='在线 IP 数量'),
        sa.Column('duration', sa.Float(), nullable=False, comment='扫描耗时（秒）'),
        sa.Column('results', sa.Text(), nullable=True, comment='扫描结果（JSON 格式）'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='扫描时间'),
        sa.ForeignKeyConstraint(['segment_id'], ['network_segments.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('ix_scan_history_id', 'scan_history', ['id'])


def downgrade() -> None:
    """
    Drop all tables
    """
    op.drop_table('scan_history')
    op.drop_table('alerts')
    op.drop_table('operation_logs')
    op.drop_table('ip_addresses')
    op.drop_table('devices')
    op.drop_table('network_segments')
    op.drop_table('users')
