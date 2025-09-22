-- Database initialization script for Polyglot Language Learning Application
-- This script sets up the initial database structure and configuration

-- =============================================================================
-- Database Configuration
-- =============================================================================

-- Set timezone to UTC
SET timezone = 'UTC';

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =============================================================================
-- Create Application User (if not exists)
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user WITH LOGIN PASSWORD 'app_password';
    END IF;
END
$$;

-- Grant necessary permissions
GRANT CONNECT ON DATABASE polyglot_db TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT CREATE ON SCHEMA public TO app_user;

-- =============================================================================
-- Create Tables
-- =============================================================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    native_language VARCHAR(10) NOT NULL DEFAULT 'TR',
    target_language VARCHAR(10) NOT NULL DEFAULT 'EN',
    proficiency_level VARCHAR(20) NOT NULL DEFAULT 'beginner',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT users_username_length CHECK (LENGTH(username) >= 3),
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_different_languages CHECK (native_language != target_language),
    CONSTRAINT users_valid_proficiency CHECK (proficiency_level IN ('beginner', 'intermediate', 'advanced', 'native', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2'))
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL DEFAULT 'Chat Session',
    session_type VARCHAR(20) NOT NULL DEFAULT 'conversation',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    source_language VARCHAR(10) NOT NULL DEFAULT 'TR',
    target_language VARCHAR(10) NOT NULL DEFAULT 'EN',
    message_count INTEGER NOT NULL DEFAULT 0,
    
    -- Legacy fields for backward compatibility
    mode VARCHAR(10),
    level VARCHAR(5),
    is_active BOOLEAN DEFAULT TRUE,
    summary TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT sessions_valid_type CHECK (session_type IN ('conversation', 'grammar', 'vocabulary', 'pronunciation')),
    CONSTRAINT sessions_valid_status CHECK (status IN ('active', 'paused', 'completed', 'archived')),
    CONSTRAINT sessions_valid_mode CHECK (mode IN ('CONVERSATION', 'GRAMMAR', 'VOCABULARY', 'tutor', 'buddy') OR mode IS NULL),
    CONSTRAINT sessions_valid_level CHECK (level IN ('A1', 'A2', 'B1', 'B2', 'C1', 'C2') OR level IS NULL)
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL DEFAULT 'user',
    content TEXT NOT NULL,
    msg_metadata JSONB,
    corrections JSONB,
    micro_exercise TEXT,
    
    -- Legacy field for backward compatibility
    role VARCHAR(10),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT messages_valid_type CHECK (message_type IN ('user', 'assistant', 'system')),
    CONSTRAINT messages_valid_role CHECK (role IN ('USER', 'ASSISTANT') OR role IS NULL),
    CONSTRAINT messages_content_not_empty CHECK (LENGTH(TRIM(content)) > 0)
);

-- =============================================================================
-- Create Indexes for Performance
-- =============================================================================

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_language_prefs ON users(native_language, target_language, proficiency_level);

-- Sessions indexes
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_active ON sessions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_mode_level ON sessions(mode, level);

-- Messages indexes
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_session_created ON messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);

-- Full-text search index for message content
CREATE INDEX IF NOT EXISTS idx_messages_content_search ON messages USING gin(to_tsvector('english', content));

-- JSONB index for corrections
CREATE INDEX IF NOT EXISTS idx_messages_corrections ON messages USING gin(corrections);

-- =============================================================================
-- Create Functions and Triggers
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_sessions_updated_at ON sessions;
CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to update session message count
CREATE OR REPLACE FUNCTION update_session_message_count()
RETURNS TRIGGER AS $
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE sessions 
        SET message_count = message_count + 1,
            updated_at = NOW()
        WHERE id = NEW.session_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE sessions 
        SET message_count = GREATEST(message_count - 1, 0),
            updated_at = NOW()
        WHERE id = OLD.session_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$ language 'plpgsql';

-- Triggers for message count
DROP TRIGGER IF EXISTS trigger_update_session_message_count_insert ON messages;
CREATE TRIGGER trigger_update_session_message_count_insert
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_session_message_count();

DROP TRIGGER IF EXISTS trigger_update_session_message_count_delete ON messages;
CREATE TRIGGER trigger_update_session_message_count_delete
    AFTER DELETE ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_session_message_count();

-- =============================================================================
-- Create Views for Common Queries
-- =============================================================================

-- Active sessions with user info
CREATE OR REPLACE VIEW active_sessions_with_users AS
SELECT 
    s.id as session_id,
    s.mode,
    s.level,
    s.created_at as session_created_at,
    u.id as user_id,
    u.username,
    u.native_language,
    u.target_language,
    u.proficiency_level
FROM sessions s
JOIN users u ON s.user_id = u.id
WHERE s.is_active = true;

-- Recent messages with session info
CREATE OR REPLACE VIEW recent_messages_with_sessions AS
SELECT 
    m.id as message_id,
    m.role,
    m.content,
    m.corrections,
    m.micro_exercise,
    m.created_at as message_created_at,
    s.id as session_id,
    s.mode,
    s.level,
    u.username
FROM messages m
JOIN sessions s ON m.session_id = s.id
JOIN users u ON s.user_id = u.id
ORDER BY m.created_at DESC;

-- =============================================================================
-- Grant Permissions to Application User
-- =============================================================================

-- Grant table permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON users TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON sessions TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON messages TO app_user;

-- Grant sequence permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Grant view permissions
GRANT SELECT ON active_sessions_with_users TO app_user;
GRANT SELECT ON recent_messages_with_sessions TO app_user;

-- =============================================================================
-- Insert Sample Data (Development Only)
-- =============================================================================

-- Check if we're in development environment
DO $$
BEGIN
    IF current_setting('server_version_num')::int >= 140000 THEN
        -- Only insert sample data if no users exist
        IF NOT EXISTS (SELECT 1 FROM users LIMIT 1) THEN
            -- Insert sample user
            INSERT INTO users (username, email, password_hash, native_language, target_language, proficiency_level)
            VALUES ('demo_user', 'demo@example.com', '$2b$12$LQv3c1yqBw2LeOiMi9rXaOEkVxaAhBxQHjLvukJUnQ.xHjLiOzZui', 'TR', 'EN', 'A2');
            
            -- Get the user ID
            DECLARE
                demo_user_id UUID;
            BEGIN
                SELECT id INTO demo_user_id FROM users WHERE username = 'demo_user';
                
                -- Insert sample session
                INSERT INTO sessions (user_id, mode, level, is_active)
                VALUES (demo_user_id, 'CONVERSATION', 'A2', true);
            END;
        END IF;
    END IF;
END
$$;

-- =============================================================================
-- Database Statistics and Maintenance
-- =============================================================================

-- Update table statistics
ANALYZE users;
ANALYZE sessions;
ANALYZE messages;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully';
    RAISE NOTICE 'Tables created: users, sessions, messages';
    RAISE NOTICE 'Indexes created for optimal performance';
    RAISE NOTICE 'Views created: active_sessions_with_users, recent_messages_with_sessions';
    RAISE NOTICE 'Permissions granted to app_user';
END
$$;