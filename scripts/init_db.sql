-- Database initialization script for the trading platform
-- This script creates the initial database structure

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS trading_platform;

-- Use the database
\c trading_platform;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create initial tables will be handled by Alembic migrations
-- This file is for any additional setup needed
