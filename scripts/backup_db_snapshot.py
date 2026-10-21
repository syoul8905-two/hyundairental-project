import urllib.request
import urllib.parse
import json
import os
import sys
import datetime

sys.stdout.reconfigure(encoding='utf-8')

SUPABASE_URL = "https://gideypynmhpjucgszyce.supabase.co"
SUPABASE_KEY = "sb_publishable_pLF_neZMUjj3G7PsiH_tuw_rfRuu8eP"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def send_heartbeat_ping():
    """Send a lightweight ping to prevent Supabase 7-day auto-pausing"""
    url = f"{SUPABASE_URL}/rest/v1/delivery_schedules?select=id&limit=1"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        t0 = datetime.datetime.now()
        with urllib.request.urlopen(req) as resp:
            elapsed = (datetime.datetime.now() - t0).total_seconds() * 1000
            print(f"  ▶ [Heartbeat Ping] 성공! (응답시간: {elapsed:.1f}ms, 상태: {resp.status}) - 7일 잠자기(Sleep) 방지 완료")
            return True
    except Exception as e:
        print(f"  ⚠️ [Heartbeat Ping] 실패: {e}")
        return False

def fetch_all_records():
    """Fetch all rows from delivery_schedules with pagination support"""
    all_rows = []
    page_size = 1000
    offset = 0

    while True:
        req_headers = HEADERS.copy()
        req_headers["Range"] = f"{offset}-{offset + page_size - 1}"
        req_headers["Prefer"] = "count=exact"
        
        url = f"{SUPABASE_URL}/rest/v1/delivery_schedules?select=*&order=id.asc"
        req = urllib.request.Request(url, headers=req_headers)
        
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if not data:
                    break
                all_rows.extend(data)
                if len(data) < page_size:
                    break
                offset += page_size
        except Exception as e:
            print(f"Error fetching page at offset {offset}: {e}")
            break

    return all_rows

def backup(output_dir="c:/antigravity/배송스케줄관리/backups"):
    os.makedirs(output_dir, exist_ok=True)
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(output_dir, f"db_snapshot_{now_str}.json")

    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Supabase 전체 데이터 백업 & 헬스체크 시작...")
    
    # 1. 7일 자동 잠자기(Auto-Pause) 방지 핑 전송
    send_heartbeat_ping()
    
    # 2. 전체 레코드 수집 및 백업
    rows = fetch_all_records()
    print(f"  ▶ 총 수집 레코드: {len(rows):,}건")

    summary = {}
    for r in rows:
        src = r.get("source_sheet") or "UNKNOWN"
        summary[src] = summary.get(src, 0) + 1

    print("  ▶ 소스 시트별 레코드 집계:")
    for src, count in sorted(summary.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"     - {src}: {count}건")

    snapshot_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "total_count": len(rows),
        "summary": summary,
        "records": rows
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(snapshot_data, f, ensure_ascii=False, indent=2)

    file_size_kb = os.path.getsize(file_path) / 1024
    print(f"✅ 백업 완료! 저장 경로: {file_path} ({file_size_kb:.1f} KB)")
    return file_path

if __name__ == "__main__":
    backup()
