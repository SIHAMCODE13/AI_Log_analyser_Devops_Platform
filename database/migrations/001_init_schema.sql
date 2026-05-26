-- =====================================================
-- AI DevOps Log Analyzer — MySQL Schema
-- Production-ready schema with indexes and constraints
-- =====================================================

CREATE DATABASE IF NOT EXISTS loganalyzer
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE loganalyzer;

-- ── Users ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          CHAR(36)     NOT NULL PRIMARY KEY,
    username    VARCHAR(64)  NOT NULL UNIQUE,
    email       VARCHAR(255) NOT NULL UNIQUE,
    is_active   TINYINT(1)   NOT NULL DEFAULT 1,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seed admin user
INSERT IGNORE INTO users (id, username, email)
VALUES ('00000000-0000-0000-0000-000000000001', 'admin', 'admin@loganalyzer.local');

-- ── Logs ──────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS logs (
    id          CHAR(36)      NOT NULL PRIMARY KEY,
    user_id     CHAR(36)      NULL,
    filename    VARCHAR(255)  NOT NULL,
    file_path   TEXT          NOT NULL,
    file_size   INT UNSIGNED  NOT NULL DEFAULT 0,
    total_lines INT UNSIGNED  NOT NULL DEFAULT 0,
    log_format  VARCHAR(50)   NULL,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY fk_logs_user (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_logs_user    (user_id),
    INDEX idx_logs_created (created_at),
    INDEX idx_logs_format  (log_format)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Analysis Results ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS analysis_results (
    id                  CHAR(36)       NOT NULL PRIMARY KEY,
    log_id              CHAR(36)       NOT NULL,
    user_id             CHAR(36)       NULL,
    status              ENUM('pending','running','completed','failed') NOT NULL DEFAULT 'pending',
    mode                VARCHAR(50)    NOT NULL DEFAULT 'auto',
    sensitivity         TINYINT        NOT NULL DEFAULT 7,
    total_lines         INT UNSIGNED   NOT NULL DEFAULT 0,
    anomaly_count       INT UNSIGNED   NOT NULL DEFAULT 0,
    anomaly_rate        DECIMAL(8,6)   NOT NULL DEFAULT 0.000000,
    top_classification  VARCHAR(100)   NULL,
    processing_time_ms  INT UNSIGNED   NOT NULL DEFAULT 0,
    ai_model_version    VARCHAR(50)    NULL,
    raw_result          LONGTEXT       NULL,
    error_message       TEXT           NULL,
    created_at          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at        DATETIME       NULL,
    FOREIGN KEY fk_results_log  (log_id)   REFERENCES logs(id)  ON DELETE CASCADE,
    FOREIGN KEY fk_results_user (user_id)  REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_results_log     (log_id),
    INDEX idx_results_status  (status),
    INDEX idx_results_created (created_at),
    INDEX idx_results_anomaly (anomaly_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
