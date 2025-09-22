#!/usr/bin/env python3
"""Complete database reset script - creates a fresh database from scratch."""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Set PYTHONPATH environment variable
os.environ['PYTHONPATH'] = str(project_root)

from sqlalchemy import text
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.config import get_settings


async def drop_all_tables(db_connection):
    """Drop all existing tables and constraints."""
    print("🗑️  Dropping all existing tables...")
    
    async with db_connection.engine.begin() as conn:
        # Drop tables in correct order (respecting foreign key constraints)
        tables_to_drop = [
            'assessment_responses',
            'assessment_sessions', 
            'messages',
            'sessions',
            'users',
            'topics',
            'schema_migrations'  # Also drop migration tracking table
        ]
        
        for table in tables_to_drop:
            try:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"  ✅ Dropped table: {table}")
            except Exception as e:
                print(f"  ⚠️  Could not drop {table}: {e}")


async def create_fresh_database(db_connection):
    """Create all tables from scratch using SQLAlchemy models."""
    print("🏗️  Creating fresh database schema...")
    
    # Import models to ensure they're registered
    from src.infrastructure.database.models import Base
    
    async with db_connection.engine.begin() as conn:
        # Create all tables from models
        await conn.run_sync(Base.metadata.create_all)
        print("  ✅ Created all tables from models")


async def create_indexes_and_constraints(db_connection):
    """Create additional indexes and constraints."""
    print("📊 Creating indexes and constraints...")
    
    async with db_connection.engine.begin() as conn:
        # User table indexes
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_username_email 
            ON users(username, email)
        """))
        
        # Session table indexes
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sessions_user_id_active 
            ON sessions(user_id, is_active)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sessions_created_at 
            ON sessions(created_at)
        """))
        
        # Message table indexes
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_messages_session_created 
            ON messages(session_id, created_at)
        """))
        
        # Assessment indexes
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_assessment_sessions_user_id 
            ON assessment_sessions(user_id)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_assessment_responses_session_id 
            ON assessment_responses(session_id)
        """))
        
        print("  ✅ Created all indexes")


async def insert_default_data(db_connection):
    """Insert default/seed data."""
    print("🌱 Inserting default data...")
    
    async with db_connection.engine.begin() as conn:
        # Insert default topics
        await conn.execute(text("""
            INSERT INTO topics (id, name, description, category, difficulty_level, keywords, conversation_starters) 
            VALUES 
            ('daily_life', 'Daily Life', 'Everyday conversations and activities', 'general', 'A1', 
             '["morning", "food", "family", "work"]'::jsonb, 
             '["How was your day?", "What did you have for breakfast?"]'::jsonb),
            ('travel', 'Travel & Tourism', 'Travel experiences and planning', 'lifestyle', 'A2', 
             '["vacation", "hotel", "airport", "sightseeing"]'::jsonb, 
             '["Where would you like to travel?", "Tell me about your last trip"]'::jsonb),
            ('business', 'Business & Work', 'Professional conversations', 'professional', 'B1', 
             '["meeting", "presentation", "colleague", "project"]'::jsonb, 
             '["How is your work going?", "What projects are you working on?"]'::jsonb)
            ON CONFLICT (id) DO NOTHING
        """))
        
        print("  ✅ Inserted default topics")


async def verify_database(db_connection):
    """Verify that the database was created correctly."""
    print("🔍 Verifying database...")
    
    async with db_connection.engine.begin() as conn:
        # Check if all tables exist
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result.fetchall()]
        expected_tables = [
            'assessment_responses', 'assessment_sessions', 'messages', 
            'sessions', 'topics', 'users'
        ]
        
        print(f"  📋 Found tables: {', '.join(tables)}")
        
        missing_tables = set(expected_tables) - set(tables)
        if missing_tables:
            print(f"  ❌ Missing tables: {', '.join(missing_tables)}")
            return False
        
        # Test basic functionality
        await conn.execute(text("SELECT 1"))
        print("  ✅ Database connection test passed")
        
        return True


async def main():
    """Main reset function."""
    print("🚀 Starting complete database reset...")
    print("⚠️  WARNING: This will delete ALL existing data!")
    
    # Ask for confirmation
    if len(sys.argv) < 2 or sys.argv[1] != "--force":
        response = input("Are you sure you want to reset the database? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Database reset cancelled")
            return 1
    
    # Initialize database connection
    settings = get_settings()
    db_connection = DatabaseConnection(settings.database_url)
    
    try:
        await db_connection.connect()
        
        # Step 1: Drop all existing tables
        await drop_all_tables(db_connection)
        
        # Step 2: Create fresh database schema
        await create_fresh_database(db_connection)
        
        # Step 3: Create indexes and constraints
        await create_indexes_and_constraints(db_connection)
        
        # Step 4: Insert default data
        await insert_default_data(db_connection)
        
        # Step 5: Verify everything worked
        if await verify_database(db_connection):
            print("🎉 Database reset completed successfully!")
            print("📝 Your database is now fresh and ready to use")
            return 0
        else:
            print("❌ Database verification failed")
            return 1
            
    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        return 1
    finally:
        await db_connection.disconnect()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)