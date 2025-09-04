-- Initialize database for TiketQ services

-- Create user_profiles table for user-service
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    date_of_birth VARCHAR(10),
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);

-- Create users table for auth-service (if not exists)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(10) DEFAULT 'user' CHECK (role IN ('user', 'admin'))
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Create index on role for faster role-based queries
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Create database and user (existing from other services)
-- CREATE DATABASE tiketq_db; -- Already exists
-- CREATE USER tiketq_user WITH PASSWORD 'tiketq_password'; -- Already exists
-- GRANT ALL PRIVILEGES ON DATABASE tiketq_db TO tiketq_user; -- Already exists

-- Connect to the tiketq database
\c tiketq_db;

-- Grant permissions for shared database access
GRANT ALL ON SCHEMA public TO tiketq_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tiketq_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tiketq_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO tiketq_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO tiketq_user;

-- Create payment-specific tables (will be created by SQLAlchemy if not exists)
-- The PaymentRecord model will create this automatically

-- Create indexes for better performance on payment queries
-- These will be created by SQLAlchemy if the tables don't exist
-- If you want to create them manually:

-- CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);
-- CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
-- CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at);
-- CREATE INDEX IF NOT EXISTS idx_payments_payment_method ON payments(payment_method);

-- You can add other service tables here as well
-- For example:

-- Users table (if managed by user-service)
-- CREATE TABLE IF NOT EXISTS users (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     email VARCHAR(255) UNIQUE NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- Transactions table (if managed by transaction-service)
-- CREATE TABLE IF NOT EXISTS transactions (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     user_id UUID REFERENCES users(id),
--     order_id VARCHAR(255) NOT NULL,
--     amount DECIMAL(15,2) NOT NULL,
--     status VARCHAR(50) NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- Orders table (might be shared across services)
-- CREATE TABLE IF NOT EXISTS orders (
--     id VARCHAR(255) PRIMARY KEY,
--     user_id UUID REFERENCES users(id),
--     total_amount DECIMAL(15,2) NOT NULL,
--     status VARCHAR(50) NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

COMMENT ON SCHEMA public IS 'TiketQ shared database schema for all microservices';