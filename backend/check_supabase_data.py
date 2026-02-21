#!/usr/bin/env python3
"""
Check that Supabase has data. Lightdash reads from this same database —
if these tables have rows, Lightdash will show data when you run queries.
Requires SUPABASE_URL and SUPABASE_KEY in .env (from backend/ or repo root).
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        print("Missing SUPABASE_URL or SUPABASE_KEY in .env")
        sys.exit(1)

    try:
        from supabase import create_client
        client = create_client(url, key)
    except Exception as e:
        print(f"Supabase client error: {e}")
        sys.exit(1)

    tables = [
        "products",
        "sales",
        "suppliers",
        "purchase_orders",
        "agent_cycles",
    ]
    print("Supabase table row counts (Lightdash reads this same DB):")
    print("-" * 50)
    all_ok = True
    for table in tables:
        try:
            r = client.table(table).select("*", count="exact").limit(1).execute()
            count = r.count if hasattr(r, "count") and r.count is not None else "?"
            if isinstance(count, int) and count == 0:
                all_ok = False
            print(f"  {table:20} {count} rows")
        except Exception as e:
            print(f"  {table:20} error: {e}")
            all_ok = False
    print("-" * 50)
    if all_ok:
        print("Data is in Supabase. In Lightdash: connect this DB as Warehouse, then Explore → pick a model → Run to see the same data.")
    else:
        print("Some tables are empty or missing. Run backend/supabase_schema.sql in Supabase SQL Editor, then python backend/seed.py to seed data.")
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
