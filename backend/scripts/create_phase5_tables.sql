CREATE TABLE IF NOT EXISTS tickets (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT DEFAULT 1 NOT NULL,
  ticket_no VARCHAR(50) UNIQUE NOT NULL,
  title VARCHAR(300) NOT NULL,
  description TEXT,
  ticket_type ENUM('ip_apply','ip_change','ip_recycle','device_onboard','device_repair','permission_apply','change_request','incident','other') NOT NULL,
  priority ENUM('low','medium','high','urgent') DEFAULT 'medium',
  status ENUM('draft','pending','in_progress','approved','rejected','completed','cancelled') DEFAULT 'draft' NOT NULL,
  applicant_id BIGINT NOT NULL,
  applicant_name VARCHAR(100),
  applicant_department VARCHAR(200),
  assignee_id BIGINT,
  assignee_name VARCHAR(100),
  related_ip VARCHAR(45),
  related_device_id INT,
  related_segment_id INT,
  form_data JSON,
  workflow_definition_id BIGINT,
  workflow_instance_id BIGINT,
  sla_deadline DATETIME,
  sla_status ENUM('normal','warning','overdue') DEFAULT 'normal',
  submitted_at DATETIME,
  completed_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_tenant (tenant_id),
  INDEX idx_status (status),
  INDEX idx_type (ticket_type),
  INDEX idx_applicant (applicant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS workflow_definitions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT DEFAULT 1 NOT NULL,
  name VARCHAR(200) NOT NULL,
  description TEXT,
  trigger_type VARCHAR(50),
  definition_json JSON NOT NULL,
  version INT DEFAULT 1,
  is_active BOOLEAN DEFAULT TRUE,
  created_by BIGINT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_tenant (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS workflow_instances (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  definition_id BIGINT NOT NULL,
  ticket_id BIGINT NOT NULL,
  status ENUM('running','completed','rejected','cancelled') DEFAULT 'running',
  current_node_id VARCHAR(100),
  history JSON,
  started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME,
  INDEX idx_definition (definition_id),
  INDEX idx_ticket (ticket_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
