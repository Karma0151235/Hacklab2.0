"""
Quick test script to validate Supabase connection before running batch scrape.
Run this to check env vars and connection before wasting time on scraping.

Usage:
    uv run python -m scraping.news.test_supabase
"""

import sys
from pathlib import Path

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scraping.news.supabase_client import test_connection, get_supabase_client
import os

def main():
    print("=" * 60)
    print("SUPABASE CONNECTION TEST")
    print("=" * 60)
    
    # Check environment variables
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    print(f"✓ SUPABASE_URL: {'SET' if url else '❌ NOT SET'}")
    print(f"✓ SUPABASE_KEY: {'SET (length: {})'.format(len(key)) if key else '❌ NOT SET'}")
    print()
    
    if not url or not key:
        print("❌ FAILED: Environment variables not configured")
        print("   Set SUPABASE_URL and SUPABASE_KEY in .env file")
        return False
    
    # Test actual connection  
    print("Testing connection to Supabase...")
    if test_connection():
        print()
        print("=" * 60)
        print("✅ ALL CHECKS PASSED - Ready to scrape!" )
        print("=" * 60)
        return True
    else:
        print()
        print("=" * 60)
        print("❌ CONNECTION TEST FAILED")
        print("=" * 60)
        print("\nCommon issues:")
        print("1. Check SUPABASE_KEY is the SERVICE ROLE key (not anon key)")
        print("2. Run the SQL migration in Supabase SQL Editor")
        print("3. Check RLS policies allow service role to INSERT")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
