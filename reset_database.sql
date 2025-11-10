-- MySQL Script to Reset BookStore Database
-- Run this with: mysql -u root -p < reset_database.sql

-- Drop existing database
DROP DATABASE IF EXISTS bookstore_db;

-- Create fresh database with proper charset
CREATE DATABASE bookstore_db 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- Verify database was created
SHOW DATABASES LIKE 'bookstore_db';

-- Show success message
SELECT 'Database bookstore_db has been reset successfully!' AS Status;
