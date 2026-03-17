from database import init_supabase

def check_jobs():
    init_supabase()
    from database import supabase
    try:
        res = supabase.table('jobs').select('*').limit(1).execute()
        if res.data:
            with open('job_cols.txt', 'w') as f:
                f.write(str(list(res.data[0].keys())))
        else:
            print("Jobs table is empty")
    except Exception as e:
        print(f"Error checking jobs: {e}")

if __name__ == "__main__":
    check_jobs()
