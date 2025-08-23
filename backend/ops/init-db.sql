-- PostgreSQL initialization script for MateHub
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant permissions to matehub user
GRANT ALL PRIVILEGES ON DATABASE matehub TO matehub;

-- Create schema if needed (tables will be created by SQLAlchemy)
-- The application will handle table creation through SQLAlchemy models
