import json, re, urllib.request, urllib.parse

with open('vehicle_log_tracker.html', 'r', encoding='utf-8') as f:
    c = f.read()

u = re.search(r'const\s+SUPABASE_URL\s*=\s*[\'"]([^\'"]+)[\'"]', c).group(1)
k = re.search(r'const\s+SUPABASE_ANON_KEY\s*=\s*[\'"]([^\'"]+)[\'"]', c).group(1)

def req_supabase(endpoint, method='GET', data=None):
    url = f"{u}/rest/v1/{endpoint}"
    headers = {
        'apikey': k,
        'Authorization': f'Bearer {k}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    encoded_data = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    with urllib.request.urlopen(req) as res:
        content = res.read().decode('utf-8')
        return json.loads(content) if content else []

c_name = urllib.parse.quote('801부8744')
rows = req_supabase(f"delivery_schedules?source_sheet=eq.VEHICLE_TRIP_LOGS&customer_name=eq.{c_name}&delivery_date=gte.2026-10-01&delivery_date=lte.2026-10-31&order=delivery_date.asc,id.asc")

print(f"Found {len(rows)} October records for 801부8744")
SHIFT = -81

for r in rows:
    r_id = r['id']
    mf = json.loads(r.get('memo_full', '{}'))
    old_start = mf.get('start_km')
    old_end = mf.get('end_km')
    new_start = old_start + SHIFT
    new_end = old_end + SHIFT
    mf['start_km'] = new_start
    mf['end_km'] = new_end
    
    # Shift stops
    stops = mf.get('stops', [])
    for s in stops:
        if s.get('start_km') is not None:
            s['start_km'] = s['start_km'] + SHIFT
        if s.get('end_km') is not None:
            s['end_km'] = s['end_km'] + SHIFT
    
    mf['stops'] = stops
    
    print(f"ID {r_id} | {r.get('delivery_date')} | Start: {old_start} -> {new_start} | End: {old_end} -> {new_end} | Dist: {mf.get('distance_km')} | Park: {mf.get('parking_fee')} | Fuel: {mf.get('fuel_fee')}")
    
    # Update Supabase
    patch_res = req_supabase(f"delivery_schedules?id=eq.{r_id}", method='PATCH', data={'memo_full': json.dumps(mf, ensure_ascii=False)})
    assert len(patch_res) == 1, f"Failed to patch {r_id}"

print("\nSuccessfully updated all 19 records with -81 km shift!")
