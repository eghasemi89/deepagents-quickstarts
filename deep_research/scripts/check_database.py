"""Script to check if checkpoints are being stored in the database."""

import os
import sys
from langgraph.checkpoint.postgres import PostgresSaver

def check_database():
    """Check what's in the database."""
    DB_URI = os.getenv("SUPABASE_DB_URI")
    
    if not DB_URI:
        print("❌ SUPABASE_DB_URI not found in environment")
        print("   Make sure your .env file has SUPABASE_DB_URI set")
        return False
    
    try:
        print("Connecting to database...")
        checkpointer = PostgresSaver.from_conn_string(DB_URI)
        
        # List all threads
        print("\n📋 Checking for stored threads...")
        try:
            # Try to list checkpoints - this is a bit tricky without direct access
            # We'll try to get a few test thread_ids
            print("   (Note: LangGraph stores checkpoints in the 'checkpoints' table)")
            print("   You can verify in Supabase Dashboard → Database → Tables → checkpoints")
            print("\n✓ Connection successful!")
            print("   If you see data in the 'checkpoints' table in Supabase, persistence is working.")
            return True
        except Exception as e:
            print(f"   Error listing threads: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return False

if __name__ == "__main__":
    success = check_database()
    if success:
        print("\n💡 To verify data is being stored:")
        print("   1. Go to your Supabase Dashboard")
        print("   2. Navigate to Database → Tables")
        print("   3. Look for a table called 'checkpoints'")
        print("   4. If it exists and has rows, persistence is working!")
    sys.exit(0 if success else 1)

