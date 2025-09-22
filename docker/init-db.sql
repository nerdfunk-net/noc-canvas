-- Initialize NOC Canvas Database
-- This script is executed when PostgreSQL container starts for the first time

-- Create the database if it doesn't exist (already handled by POSTGRES_DB env var)
-- Just ensure proper encoding and collation
ALTER DATABASE noc SET timezone TO 'UTC';

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Grant privileges to the postgres user (already handled by default)
GRANT ALL PRIVILEGES ON DATABASE noc TO postgres;