"""Cleanup script to remove old PostgresSaver schema before using langgraph up.

This script drops the tables created by PostgresSaver.setup() so that
langgraph up can create its own schema with the correct migrations.

Run this once if you're switching from PostgresSaver to langgraph up:
    uv run python cleanup_old_schema.py
"""

import os
import sys
from pathlib import Path

# Load .env file
env_path = Path(".env")
if env_path.exists():
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value

try:
    import psycopg
except ImportError:
    print("Error: psycopg is not installed.")
    print("Install it with: uv sync")
    sys.exit(1)


def cleanup_old_schema():
    """Drop old PostgresSaver tables."""
    # Get database connection string
    DB_URI = os.getenv("POSTGRES_URI_CUSTOM") or os.getenv("POSTGRES_URI") or os.getenv("SUPABASE_DB_URI")
    
    if not DB_URI:
        print("Error: No database connection string found.")
        print("Please set POSTGRES_URI_CUSTOM, POSTGRES_URI, or SUPABASE_DB_URI in your .env file.")
        sys.exit(1)
    
    try:
        print(f"Connecting to database...")
        print(f"Connection: postgresql://postgres:***@{DB_URI.split('@')[1] if '@' in DB_URI else 'hidden'}")
        
        # Connect to database
        conn = psycopg.connect(DB_URI)
        cur = conn.cursor()
        
        # Drop tables in correct order (respecting foreign keys)
        # Also drop migration tracking tables
        tables_to_drop = [
            "checkpoints",
            "checkpoint_writes",
            "checkpoint_blobs",
            "threads",
            "langgraph_migrations",  # Migration tracking table
            "migrations",  # Alternative migration tracking table name
        ]
        
        print("\n⚠️  WARNING: This will delete all existing checkpoints and threads!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            sys.exit(0)
        
        print("\nDropping old tables...")
        for table in tables_to_drop:
            try:
                cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                print(f"  ✓ Dropped table: {table}")
            except Exception as e:
                print(f"  ⚠️  Could not drop {table}: {e}")
        
        # Drop any sequences
        cur.execute("""
            DO $$ 
            DECLARE 
                r RECORD;
            BEGIN
                FOR r IN (SELECT sequence_name FROM information_schema.sequences 
                         WHERE sequence_schema = 'public') 
                LOOP
                    EXECUTE 'DROP SEQUENCE IF EXISTS ' || quote_ident(r.sequence_name) || ' CASCADE';
                END LOOP;
            END $$;
        """)
        print("  ✓ Dropped sequences")
        
        # Drop any remaining LangGraph-related tables (in case of different naming)
        cur.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND (tablename LIKE '%checkpoint%' 
                 OR tablename LIKE '%thread%' 
                 OR tablename LIKE '%migration%'
                 OR tablename LIKE '%langgraph%')
        """)
        remaining_tables = cur.fetchall()
        if remaining_tables:
            print("\nDropping additional LangGraph-related tables...")
            for (table_name,) in remaining_tables:
                try:
                    cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
                    print(f"  ✓ Dropped table: {table_name}")
                except Exception as e:
                    print(f"  ⚠️  Could not drop {table_name}: {e}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("\n✓ Old schema cleaned up successfully!")
        print("You can now run 'langgraph up' and it will create the correct schema.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("  1. Verify your connection string is correct")
        print("  2. Check that your Supabase database is accessible")
        print("  3. Ensure you have the correct database password")
        sys.exit(1)


if __name__ == "__main__":
    cleanup_old_schema()

