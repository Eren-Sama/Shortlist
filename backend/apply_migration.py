"""Apply database migrations to Supabase using the service-role key."""
import os
import sys
import httpx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    sys.exit(1)

def run_sql(sql: str) -> dict:
    """Execute raw SQL via Supabase's pg-meta REST endpoint."""
    url = f"{SUPABASE_URL}/rest/v1/rpc"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    
    wrapper_sql = f"""
    DO $$
    BEGIN
        {sql}
    END;
    $$ LANGUAGE plpgsql;
    """
    
    print("Attempting to apply migration...")
    return {}


def apply_via_postgrest_rpc(sql_statements: list[str]):
    """Apply SQL statements one at a time via PostgREST."""
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    
    for i, stmt in enumerate(sql_statements):
        stmt = stmt.strip()
        if not stmt or stmt.startswith("--"):
            continue
        print(f"  Executing statement {i+1}...")
        resp = httpx.post(
            f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
            headers=headers,
            json={"query": stmt},
            timeout=30,
        )
        if resp.status_code >= 400:
            print(f"  WARNING: Statement {i+1} returned {resp.status_code}: {resp.text}")


if __name__ == "__main__":
    migration_file = Path(__file__).parent / "migrations" / "001_initial_schema.sql"
    if not migration_file.exists():
        print(f"ERROR: Migration file not found: {migration_file}")
        sys.exit(1)
    
    sql = migration_file.read_text(encoding="utf-8")
    print(f"Loaded migration: {migration_file.name} ({len(sql)} chars)")
    print("NOTE: Please run this SQL in your Supabase SQL Editor at:")
    print(f"  https://supabase.com/dashboard/project/qmnbccollzievdydqxzq/sql/new")
    print()
    print("The SQL has been saved to: migrations/001_initial_schema.sql")
