#!/usr/bin/env python3
"""Database initialization script."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.infrastructure.database.migrations import initialize_database, reset_database
from src.infrastructure.database.connection import db_connection


async def main():
    """Main initialization function."""
    try:
        print("Initializing database...")
        
        # Connect to database first
        await db_connection.connect()
        
        await initialize_database()
        
        # Test connection
        print("Testing database connection...")
        health = await db_connection.health_check()
        if health:
            print("✅ Database connection is healthy")
        else:
            print("❌ Database connection failed")
            return 1
        
        print("✅ Database initialization completed successfully")
        return 0
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return 1
    finally:
        await db_connection.disconnect()


async def reset():
    """Reset database function - complete fresh start."""
    try:
        print("🚀 Resetting database to fresh state...")
        print("⚠️  WARNING: This will delete ALL existing data!")
        
        # Connect to database first
        await db_connection.connect()
        
        # Use the enhanced reset that drops everything
        await reset_database()
        
        # Also run initialization to ensure everything is set up
        await initialize_database()
        
        print("✅ Database reset and initialization completed successfully")
        print("📝 Your database is now fresh and ready to use")
        return 0
        
    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        return 1
    finally:
        await db_connection.disconnect()


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "init"
    
    if command == "init":
        exit_code = asyncio.run(main())
    elif command == "reset":
        exit_code = asyncio.run(reset())
    else:
        print("Usage: python init_db.py [init|reset]")
        exit_code = 1
    
    sys.exit(exit_code)