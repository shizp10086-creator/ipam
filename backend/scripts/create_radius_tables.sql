-- FreeRADIUS 认证相关表（在 IPAM 数据库中）
-- FreeRADIUS SQL 模块直接读写这些表
-- IPAM 后端 API 管理这些表的数据

-- RADIUS 用户表（802.1X 账号密码认证）
CREATE TABLE IF NOT EXISTS radius_users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tenant_id BIGINT DEFAULT 1 NOT NULL,
    username VARCHAR(100) NOT NULL UNIQUE COMMENT '用户名（802.1X 账号）',
    password VARCHAR(255) NOT NULL COMMENT '密码（明文，FreeRADIUS 需要）',
    user_type ENUM('employee', 'visitor', 'device') DEFAULT 'employee' COMMENT '用户类型',
    real_name VARCHAR(100) COMMENT '真实姓名',
    department VARCHAR(200) COMMENT '部门',
    phone VARCHAR(20),
    email VARCHAR(200),
    vlan_id INT COMMENT '分配的 VLAN',
    acl_name VARCHAR(100) COMMENT '下发的 ACL 名称',
    bandwidth_up INT COMMENT '上行带宽限制(Kbps)',
    bandwidth_down INT COMMENT '下行带宽限制(Kbps)',
    is_active BOOLEAN DEFAULT TRUE,
    expire_at DATETIME COMMENT '账号过期时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_active (is_active),
    INDEX idx_type (user_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='RADIUS 认证用户表';

-- RADIUS 回复属性表（认证通过后下发给交换机的属性）
CREATE TABLE IF NOT EXISTS radius_reply (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL COMMENT '关联用户名',
    attribute VARCHAR(100) NOT NULL COMMENT 'RADIUS 属性名',
    op VARCHAR(10) DEFAULT ':=' COMMENT '操作符',
    value VARCHAR(255) NOT NULL COMMENT '属性值',
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='RADIUS 回复属性表';

-- MAC 地址认证表（哑终端免密认证）
CREATE TABLE IF NOT EXISTS radius_mac_auth (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tenant_id BIGINT DEFAULT 1 NOT NULL,
    mac_address VARCHAR(17) NOT NULL UNIQUE COMMENT 'MAC 地址（格式 AA:BB:CC:DD:EE:FF）',
    device_name VARCHAR(200) COMMENT '设备名称',
    device_type ENUM('printer', 'camera', 'phone', 'iot', 'other') DEFAULT 'other',
    location VARCHAR(500) COMMENT '安装位置',
    vlan_id INT COMMENT '分配的 VLAN',
    acl_name VARCHAR(100) COMMENT '下发的 ACL',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_mac (mac_address),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='MAC 地址认证白名单';

-- RADIUS NAS 设备表（交换机/AC 注册）
CREATE TABLE IF NOT EXISTS radius_nas_devices (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tenant_id BIGINT DEFAULT 1 NOT NULL,
    name VARCHAR(200) NOT NULL COMMENT '设备名称',
    ip_address VARCHAR(45) NOT NULL UNIQUE COMMENT '设备管理 IP',
    secret VARCHAR(100) NOT NULL COMMENT 'RADIUS 共享密钥',
    nas_type ENUM('huawei', 'h3c', 'ruijie', 'cisco', 'other') DEFAULT 'huawei',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ip (ip_address)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='RADIUS NAS 设备注册表';

-- RADIUS 计费记录表
CREATE TABLE IF NOT EXISTS radius_accounting (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) NOT NULL,
    username VARCHAR(100),
    mac_address VARCHAR(17),
    ip_address VARCHAR(45),
    nas_ip VARCHAR(45),
    nas_port VARCHAR(50),
    start_time DATETIME,
    stop_time DATETIME,
    session_time INT COMMENT '会话时长(秒)',
    input_octets BIGINT DEFAULT 0 COMMENT '上行流量(字节)',
    output_octets BIGINT DEFAULT 0 COMMENT '下行流量(字节)',
    status ENUM('start', 'stop', 'alive') DEFAULT 'start',
    INDEX idx_session (session_id),
    INDEX idx_username (username),
    INDEX idx_start (start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='RADIUS 计费记录';

-- RADIUS 认证日志表
CREATE TABLE IF NOT EXISTS radius_auth_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100),
    mac_address VARCHAR(17),
    ip_address VARCHAR(45),
    nas_ip VARCHAR(45),
    nas_port VARCHAR(50),
    auth_result VARCHAR(50) COMMENT '认证结果',
    reply_message VARCHAR(500),
    auth_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_mac (mac_address),
    INDEX idx_time (auth_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='RADIUS 认证日志';

-- 插入默认测试数据
INSERT IGNORE INTO radius_users (username, password, user_type, real_name, department, vlan_id, is_active)
VALUES ('testuser', 'test123', 'employee', '测试用户', '研发部', 100, 1);

INSERT IGNORE INTO radius_reply (username, attribute, op, value) VALUES
('testuser', 'Tunnel-Type', ':=', 'VLAN'),
('testuser', 'Tunnel-Medium-Type', ':=', 'IEEE-802'),
('testuser', 'Tunnel-Private-Group-Id', ':=', '100');
