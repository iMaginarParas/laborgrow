from database import supabase
import json

def dump_worker():
    res = supabase.table('employees').select('*').eq('id', 'cf688a6d-feaf-46b6-9026-6081c41ab5e1').execute()
    with open('worker_data.json', 'w') as f:
        json.dump(res.data, f, indent=2)

if __name__ == "__main__":
    dump_worker()
