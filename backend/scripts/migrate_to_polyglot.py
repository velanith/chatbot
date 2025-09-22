#!/usr/bin/env python3
"""Migration script for polyglot rebranding - migrate from language_learning_db to polyglot_db."""

import asyncio
import sys
import os
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import asyncpg

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Set PYTHONPATH environment variable
os.environ['PYTHONPATH'] = str(project_root)

from src.infrastructure.config import get_settings


class PolyglotMigrator:
    """Handles migration from language_learning_db to polyglot_db."""
    
    def __init__(self, dry_run: bool = False):
        """Initialize migrator."""
        self.dry_run = dry_run
        self.settings = get_settings()
        self.backup_dir = Path(__file__).parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Parse database URLs to get connection details
        base_url = self.settings.database_url
        
        # Convert SQLAlchemy URL to asyncpg URL format
        if "postgresql+asyncpg://" in base_url:
            base_url = base_url.replace("postgresql+asyncpg://", "postgresql://")
        
        # Create old and new database URLs
        if "polyglot_db" in base_url:
            self.new_db_url = base_url
            self.old_db_url = base_url.replace("polyglot_db", "language_learning_db")
        else:
            self.old_db_url = base_url
            self.new_db_url = base_url.replace("language_learning_db", "polyglot_db")
        
        # Extract connection details
        self.db_host, self.db_port, self.db_user, self.db_password = self._parse_db_url(self.old_db_url)
        
        print(f"🔧 Migration mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"📊 Source database: language_learning_db")
        print(f"🎯 Target database: polyglot_db")
    
    def _parse_db_url(self, db_url: str) -> tuple:
        """Parse database URL to extract connection details."""
        # Example: postgresql://user:password@localhost:5432/database
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)
        return parsed.hostname, parsed.port or 5432, parsed.username, parsed.password
    
    async def check_source_database_exists(self) -> bool:
        """Check if source database exists."""
        try:
            conn = await asyncpg.connect(self.old_db_url)
            await conn.close()
            return True
        except Exception as e:
            print(f"❌ Source database not accessible: {e}")
            return False
    
    async def check_target_database_exists(self) -> bool:
        """Check if target database exists."""
        try:
            conn = await asyncpg.connect(self.new_db_url)
            await conn.close()
            return True
        except Exception:
            return False
    
    async def create_backup(self) -> str:
        """Create backup of source database."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"language_learning_db_backup_{timestamp}.sql"
        
        print(f"📦 Creating backup: {backup_file}")
        
        if self.dry_run:
            print("🔍 DRY RUN: Would create backup with pg_dump")
            # Create a dummy backup file for dry run
            backup_file.write_text("-- DRY RUN BACKUP FILE")
            return str(backup_file)
        
        # Use pg_dump to create backup
        cmd = [
            "pg_dump",
            "-h", self.db_host,
            "-p", str(self.db_port),
            "-U", self.db_user,
            "-d", "language_learning_db",
            "-f", str(backup_file),
            "--verbose",
            "--no-password"
        ]
        
        # Set password environment variable
        env = os.environ.copy()
        if self.db_password:
            env["PGPASSWORD"] = self.db_password
        
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            print(f"✅ Backup created successfully: {backup_file}")
            return str(backup_file)
        except subprocess.CalledProcessError as e:
            print(f"❌ Backup failed: {e}")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            raise
    
    async def create_target_database(self) -> None:
        """Create target database if it doesn't exist."""
        print("🏗️ Preparing target database: polyglot_db")
        
        if self.dry_run:
            print("🔍 DRY RUN: Would create polyglot_db database")
            return
        
        # Connect to postgres database to create new database
        postgres_url = self.old_db_url.replace("/language_learning_db", "/postgres")
        
        try:
            conn = await asyncpg.connect(postgres_url)
            
            # Check if database already exists
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = 'polyglot_db'"
            )
            
            if exists:
                print("ℹ️ Target database exists, dropping and recreating for clean migration")
                
                # Terminate connections to the database
                await conn.execute("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = 'polyglot_db' AND pid <> pg_backend_pid()
                """)
                
                # Drop and recreate database
                await conn.execute("DROP DATABASE polyglot_db")
                await conn.execute("CREATE DATABASE polyglot_db")
                print("✅ Target database recreated successfully")
            else:
                await conn.execute("CREATE DATABASE polyglot_db")
                print("✅ Target database created successfully")
            
            await conn.close()
            
        except Exception as e:
            print(f"❌ Failed to create target database: {e}")
            raise
    
    async def restore_backup_to_target(self, backup_file: str) -> None:
        """Restore backup to target database."""
        print(f"📥 Restoring backup to polyglot_db: {backup_file}")
        
        if self.dry_run:
            print("🔍 DRY RUN: Would restore backup to polyglot_db")
            return
        
        # Use psql to restore backup
        cmd = [
            "psql",
            "-h", self.db_host,
            "-p", str(self.db_port),
            "-U", self.db_user,
            "-d", "polyglot_db",
            "-f", backup_file,
            "--quiet"
        ]
        
        # Set password environment variable
        env = os.environ.copy()
        if self.db_password:
            env["PGPASSWORD"] = self.db_password
        
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            print("✅ Backup restored successfully to polyglot_db")
        except subprocess.CalledProcessError as e:
            print(f"❌ Restore failed: {e}")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            raise
    
    async def verify_migration(self) -> bool:
        """Verify that migration was successful."""
        print("🔍 Verifying migration...")
        
        if self.dry_run:
            print("🔍 DRY RUN: Would verify migration by comparing table counts")
            return True
        
        try:
            # Connect to both databases
            old_conn = await asyncpg.connect(self.old_db_url)
            new_conn = await asyncpg.connect(self.new_db_url)
            
            # Get table counts from both databases
            old_tables = await old_conn.fetch("""
                SELECT table_name, 
                       (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from %I.%I', table_schema, table_name), false, true, '')))[1]::text::int as row_count
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            new_tables = await new_conn.fetch("""
                SELECT table_name,
                       (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from %I.%I', table_schema, table_name), false, true, '')))[1]::text::int as row_count
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            await old_conn.close()
            await new_conn.close()
            
            # Compare table counts
            old_data = {row['table_name']: row['row_count'] for row in old_tables}
            new_data = {row['table_name']: row['row_count'] for row in new_tables}
            
            print("📊 Table comparison:")
            print("-" * 50)
            
            all_tables = set(old_data.keys()) | set(new_data.keys())
            verification_passed = True
            
            for table in sorted(all_tables):
                old_count = old_data.get(table, 0)
                new_count = new_data.get(table, 0)
                status = "✅" if old_count == new_count else "❌"
                
                if old_count != new_count:
                    verification_passed = False
                
                print(f"{status} {table}: {old_count} -> {new_count}")
            
            if verification_passed:
                print("✅ Migration verification passed!")
            else:
                print("❌ Migration verification failed!")
            
            return verification_passed
            
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False
    
    async def test_application_connectivity(self) -> bool:
        """Test that application can connect to new database."""
        print("🔌 Testing application connectivity to polyglot_db...")
        
        if self.dry_run:
            print("🔍 DRY RUN: Would test application connectivity")
            return True
        
        try:
            # Test basic connection
            conn = await asyncpg.connect(self.new_db_url)
            
            # Test basic queries
            result = await conn.fetchval("SELECT COUNT(*) FROM users")
            print(f"✅ Connected successfully. Found {result} users in polyglot_db")
            
            await conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Application connectivity test failed: {e}")
            return False
    
    async def rollback_migration(self, backup_file: str) -> None:
        """Rollback migration by restoring from backup."""
        print(f"🔄 Rolling back migration using backup: {backup_file}")
        
        if self.dry_run:
            print("🔍 DRY RUN: Would rollback migration")
            return
        
        if not Path(backup_file).exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        try:
            # Drop and recreate source database
            postgres_url = self.old_db_url.replace("/language_learning_db", "/postgres")
            conn = await asyncpg.connect(postgres_url)
            
            # Terminate connections to the database
            await conn.execute("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = 'language_learning_db' AND pid <> pg_backend_pid()
            """)
            
            # Drop and recreate database
            await conn.execute("DROP DATABASE IF EXISTS language_learning_db")
            await conn.execute("CREATE DATABASE language_learning_db")
            
            await conn.close()
            
            # Restore from backup
            cmd = [
                "psql",
                "-h", self.db_host,
                "-p", str(self.db_port),
                "-U", self.db_user,
                "-d", "language_learning_db",
                "-f", backup_file,
                "--quiet"
            ]
            
            env = os.environ.copy()
            if self.db_password:
                env["PGPASSWORD"] = self.db_password
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            print("✅ Rollback completed successfully")
            
        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            raise
    
    async def migrate(self) -> str:
        """Execute the complete migration process."""
        print("🚀 Starting polyglot database migration...")
        
        # Check prerequisites
        if not await self.check_source_database_exists():
            raise Exception("Source database (language_learning_db) not accessible")
        
        # Create backup
        backup_file = await self.create_backup()
        
        # Create target database
        await self.create_target_database()
        
        # Restore backup to target
        await self.restore_backup_to_target(backup_file)
        
        # Verify migration
        if not await self.verify_migration():
            raise Exception("Migration verification failed")
        
        # Test application connectivity
        if not await self.test_application_connectivity():
            raise Exception("Application connectivity test failed")
        
        print("🎉 Migration completed successfully!")
        return backup_file


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Polyglot database migration tool")
    parser.add_argument("command", choices=["migrate", "rollback", "dry-run", "test-rollback"],
                       help="Migration command to run")
    parser.add_argument("--backup-file", help="Backup file for rollback")
    
    args = parser.parse_args()
    
    try:
        if args.command == "dry-run":
            migrator = PolyglotMigrator(dry_run=True)
            backup_file = await migrator.migrate()
            print(f"🔍 Dry run completed. Backup file would be: {backup_file}")
            
        elif args.command == "migrate":
            migrator = PolyglotMigrator(dry_run=False)
            backup_file = await migrator.migrate()
            print(f"💾 Backup file created: {backup_file}")
            print("⚠️ Keep this backup file safe for potential rollback!")
            
        elif args.command == "rollback":
            if not args.backup_file:
                print("❌ Backup file is required for rollback")
                sys.exit(1)
            
            migrator = PolyglotMigrator(dry_run=False)
            await migrator.rollback_migration(args.backup_file)
            
        elif args.command == "test-rollback":
            if not args.backup_file:
                print("❌ Backup file is required for rollback test")
                sys.exit(1)
            
            migrator = PolyglotMigrator(dry_run=True)
            await migrator.rollback_migration(args.backup_file)
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())