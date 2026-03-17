from database import get_supabase
import os
from dotenv import load_dotenv

load_dotenv()

def check_schema():
    supabase = get_supabase()
    tables = ['employees', 'employers', 'jobs', 'job_applications', 'bookings', 'reviews']
    
    print("--- Database Schema Inspection ---")
    for table in tables:
        try:
            # Fetch one row to get columns
            res = supabase.table(table).select("*").limit(1).execute()
            if res.data:
                columns = list(res.data[0].keys())
                print(f"Table '{table}': OK. Columns: {columns}")
                if table == 'jobs':
                    # specifically check for employer_id or created_by
                    pass
            else:
                print(f"Table '{table}': EXISTS but EMPTY.")
                # Try to get columns anyway via an illegal query that might reveal them in error
                try:
                    supabase.table(table).insert({"_non_existent_column_": "val"}).execute()
                except Exception as e:
                    # Sometimes error messages contain column hints, but not always with Supabase/PostgREST
                    print(f"  (Empty table, couldn't determine columns from data)")
        except Exception as e:
            if "not found" in str(e).lower() or "cache" in str(e).lower() or "does not exist" in str(e).lower():
                print(f"Table '{table}': MISSING")
            else:
                print(f"Table '{table}': ERROR - {str(e)[:100]}")

if __name__ == "__main__":
    check_schema()
