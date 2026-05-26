-- =====================================================
-- AI DevOps Log Analyzer — Development Seed Data
-- Run after 001_init_schema.sql to populate test data
-- Usage: mysql -u loguser -plogpass loganalyzer < seed_dev.sql
-- =====================================================

USE loganalyzer;

-- Seed a default admin user (already inserted in schema, this is idempotent)
INSERT IGNORE INTO users (id, username, email, is_active)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'admin', 'admin@loganalyzer.local', 1),
  ('00000000-0000-0000-0000-000000000002', 'devuser', 'dev@loganalyzer.local', 1);

-- Note: Log file records are NOT seeded here because they reference
-- actual files on disk. Upload files via the UI or API to generate them.
