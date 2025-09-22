-- Initialize Polyglot Database
CREATE DATABASE polyglot_db;
CREATE USER polyglot_user WITH ENCRYPTED PASSWORD 'polyglot_password';
GRANT ALL PRIVILEGES ON DATABASE polyglot_db TO polyglot_user;