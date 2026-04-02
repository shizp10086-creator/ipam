CREATE TABLE IF NOT EXISTS racks (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT DEFAULT 1 NOT NULL,
  datacenter_id BIGINT NOT NULL,
  name VARCHAR(100) NOT NULL,
  total_u INT DEFAULT 42 NOT NULL,
  used_u INT DEFAULT 0,
  rated_power DECIMAL(10,2),
  current_power DECIMAL(10,2) DEFAULT 0,
  max_weight DECIMAL(10,2),
  `row_number` VARCHAR(20),
  `column_number` VARCHAR(20),
  description TEXT,
  custom_fields JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_tenant (tenant_id),
  INDEX idx_dc (datacenter_id),
  FOREIGN KEY (datacenter_id) REFERENCES datacenters(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS rack_installations (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  rack_id BIGINT NOT NULL,
  device_id INT NOT NULL,
  start_u INT NOT NULL,
  u_size INT NOT NULL,
  face ENUM('front','rear') DEFAULT 'front',
  power_consumption DECIMAL(10,2),
  pdu_port VARCHAR(50),
  installed_by BIGINT,
  installed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  uninstalled_at DATETIME,
  status ENUM('installed','uninstalled') DEFAULT 'installed',
  INDEX idx_rack (rack_id),
  INDEX idx_device (device_id),
  FOREIGN KEY (rack_id) REFERENCES racks(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS vlans (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT DEFAULT 1 NOT NULL,
  vlan_id INT NOT NULL,
  name VARCHAR(200) NOT NULL,
  description TEXT,
  group_name VARCHAR(200),
  segment_ids JSON,
  custom_fields JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_tenant (tenant_id),
  INDEX idx_vlan_id (vlan_id),
  UNIQUE KEY uk_tenant_vlan (tenant_id, vlan_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cable_connections (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT DEFAULT 1 NOT NULL,
  device_a_id INT,
  port_a VARCHAR(100) NOT NULL,
  device_b_id INT,
  port_b VARCHAR(100) NOT NULL,
  cable_type ENUM('fiber','copper','dac'),
  cable_number VARCHAR(100),
  cable_length DECIMAL(10,2),
  status ENUM('active','inactive') DEFAULT 'active',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_tenant (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
