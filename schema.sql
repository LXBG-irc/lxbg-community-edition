CREATE TABLE IF NOT EXISTS ls_users (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(32) NOT NULL,
  username_normalized VARCHAR(32) NOT NULL,
  email VARCHAR(190) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  status ENUM('active','suspended','deleted') NOT NULL DEFAULT 'active',
  role ENUM('user','moderator','admin','owner') NOT NULL DEFAULT 'user',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_ls_users_username_normalized (username_normalized),
  UNIQUE KEY uq_ls_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ls_nicknames (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  nickname VARCHAR(32) NOT NULL,
  nickname_normalized VARCHAR(32) NOT NULL,
  is_primary TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_ls_nicknames_normalized (nickname_normalized),
  KEY idx_ls_nicknames_user (user_id),
  CONSTRAINT fk_ls_nicknames_user FOREIGN KEY (user_id) REFERENCES ls_users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ls_channels (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  channel_name VARCHAR(64) NOT NULL,
  channel_name_normalized VARCHAR(64) NOT NULL,
  founder_user_id BIGINT UNSIGNED NOT NULL,
  topic VARCHAR(512) NULL,
  modes VARCHAR(255) NOT NULL DEFAULT '+nt',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_ls_channels_name (channel_name_normalized),
  CONSTRAINT fk_ls_channels_founder FOREIGN KEY (founder_user_id) REFERENCES ls_users(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ls_channel_access (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  channel_id BIGINT UNSIGNED NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  access_role ENUM('founder','admin','op','halfop','voice','member') NOT NULL DEFAULT 'member',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_ls_channel_access (channel_id,user_id),
  CONSTRAINT fk_ls_channel_access_channel FOREIGN KEY (channel_id) REFERENCES ls_channels(id) ON DELETE CASCADE,
  CONSTRAINT fk_ls_channel_access_user FOREIGN KEY (user_id) REFERENCES ls_users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ls_sessions (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  token_hash CHAR(64) NOT NULL,
  expires_at DATETIME NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_ls_sessions_token (token_hash),
  CONSTRAINT fk_ls_sessions_user FOREIGN KEY (user_id) REFERENCES ls_users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ls_irc_auth_tokens (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  token_hash CHAR(64) NOT NULL,
  purpose ENUM('sasl','webchat','client') NOT NULL DEFAULT 'sasl',
  used_at DATETIME NULL,
  expires_at DATETIME NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_ls_irc_auth_tokens_token (token_hash),
  CONSTRAINT fk_ls_irc_auth_tokens_user FOREIGN KEY (user_id) REFERENCES ls_users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ls_modules (
  module_key VARCHAR(64) PRIMARY KEY,
  enabled TINYINT(1) NOT NULL DEFAULT 0,
  config_json JSON NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ls_cam_permissions (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  channel_id BIGINT UNSIGNED NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  can_view TINYINT(1) NOT NULL DEFAULT 1,
  can_publish TINYINT(1) NOT NULL DEFAULT 1,
  is_banned TINYINT(1) NOT NULL DEFAULT 0,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_ls_cam_permissions (channel_id,user_id),
  CONSTRAINT fk_ls_cam_permissions_channel FOREIGN KEY (channel_id) REFERENCES ls_channels(id) ON DELETE CASCADE,
  CONSTRAINT fk_ls_cam_permissions_user FOREIGN KEY (user_id) REFERENCES ls_users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO ls_modules (module_key,enabled,config_json) VALUES
('nickname',1,NULL),('channel',1,NULL),('cam_hooks',1,NULL)
ON DUPLICATE KEY UPDATE module_key=VALUES(module_key);
