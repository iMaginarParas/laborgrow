import asyncio
import httpx

async def test():
    url = 'https://bixrgczukyudjoprsjyp.supabase.co/rest/v1/admin_users?select=*'
    anon_key = 'sb_publishable_oqeIi7MymSXHWuiCNgs6mA_pyNbnvSy'
    service_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJpeHJnY3p1a3l1ZGpvcHJzanlwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTMxNjIxMCwiZXhwIjoyMDg2ODkyMjEwfQ.JK8Tv0-Be-xNRpiFfXMSrcJJ-uwQ9xImhCF6JYEcYRM'
    
    async with httpx.AsyncClient() as client:
        anon_resp = await client.get(url, headers={'apikey': anon_key, 'Authorization': f'Bearer {anon_key}'})
        print('Anon:', anon_resp.json())
        
        service_resp = await client.get(url, headers={'apikey': service_key, 'Authorization': f'Bearer {service_key}'})
        print('Service:', service_resp.json())

asyncio.run(test())
