-- SENTINEL Database Initialization
-- This file is run automatically when the PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- for text search

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE sentinel_db TO sentinel;

-- Create indexes for performance (tables are created by SQLAlchemy)
-- These will be added after tables are created by the application
