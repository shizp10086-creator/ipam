CREATE TABLE IF NOT EXISTS collector_credentials (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT DEFAULT 1 NOT NULL,
  name VARCHAR(200) NOT NULL,
  credential_type ENUM('snmp_v2c','snmp_v3','ssh_password','ssh_key','wmi','api_key') NOT NULL,
  credential_data JSON NOT NULL,
  description TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_tenant (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS collector_tasks (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT DEFAULT 1 NOT NULL,
  name VARCHAR(200) NOT NULL,
  protocol ENUM('snmp','ssh','ping','syslog','netflow','wmi','modbus','mqtt','ipmi') NOT NULL,
  targets JSON NOT NULL,
  credential_id BIGINT,
  config JSON,
  interval_seconds INT DEFAULT 300,
  timeout_seconds INT DEFAULT 30,
  retry_count INT DEFAULT 2,
  priority INT DEFAULT 5,
  is_active BOOLEAN DEFAULT TRUE,
  last_run_at DATETIME,
  last_run_status VARCHAR(20),
  last_run_duration_ms INT,
  total_runs INT DEFAULT 0,
  success_runs INT DEFAULT 0,
  fail_runs INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_tenant (tenant_id),
  INDEX idx_protocol (protocol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS collector_task_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  task_id BIGINT NOT NULL,
  status ENUM('success','failed','timeout','partial') NOT NULL,
  target_count INT,
  success_count INT DEFAULT 0,
  fail_count INT DEFAULT 0,
  duration_ms INT,
  error_message TEXT,
  details JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
  INDEX idx_task (task_id),
  INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
