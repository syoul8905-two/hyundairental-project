# -*- coding: utf-8 -*-
import sys, os
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

artifact_dir = r"C:\Users\User\.gemini\antigravity\brain\da63d277-3302-44bf-9782-450f6c45bd72"
page_errors = []
console_errors = []

def run_wtt():
    with sync_playwright() as p:
        print('[1] Chromium (Chrome channel) 브라우저 구동...')
        browser = p.chromium.launch(channel='chrome', headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()

        page.on('pageerror', lambda err: page_errors.append(f'[PAGE ERROR] {err}'))
        page.on('console', lambda msg: console_errors.append(f'[{msg.type}] {msg.text}') if msg.type in ['error'] else None)

        print('\n[2] http://localhost:8080/vehicle_log_tracker.html 접속 중...')
        page.goto('http://localhost:8080/vehicle_log_tracker.html', wait_until='networkidle')
        page.wait_for_timeout(3000)

        print('[3] 801부8744 차량 및 2026년 10월 선택 상태 확인...')
        page.evaluate('''() => {
            selectVehicle('801부8744');
            shiftMonth(-1);
        }''')
        page.wait_for_timeout(3000)

        # Evaluate KPI card values from DOM
        kpi_res = page.evaluate('''() => {
            return {
                prevMonthKm: document.getElementById('kpiPrevMonthKm').innerText.trim(),
                currentMonthKm: document.getElementById('kpiCurrentMonthKm').innerText.trim(),
                totalDistanceKm: document.getElementById('kpiTotalDistanceKm').innerText.trim(),
                operatingDays: document.getElementById('kpiOperatingDays').innerText.trim(),
                totalParkingFee: document.getElementById('kpiTotalParkingFee').innerText.trim(),
                parkingCount: document.getElementById('kpiParkingCount').innerText.trim(),
                totalFuelFee: document.getElementById('kpiTotalFuelFee').innerText.trim(),
                fuelCount: document.getElementById('kpiFuelCount').innerText.trim(),
                tripLogsCount: tripLogs.length,
                rowsCount: document.querySelectorAll('#tripLogTableBody tr').length
            };
        }''')

        print('\n--- [4] DOM 렌더링 KPI 실측 결과 ---')
        print(f"전월말 계기판: {kpi_res['prevMonthKm']} (기대값: 72,255 km)")
        print(f"당월말 계기판: {kpi_res['currentMonthKm']} (기대값: 73,865 km)")
        print(f"총 주행거리: {kpi_res['totalDistanceKm']} (기대값: 1,610 km)")
        print(f"운행일수: {kpi_res['operatingDays']} (기대값: 운행 19일 / 미운행 0일)")
        print(f"주차비 합계: {kpi_res['totalParkingFee']} ({kpi_res['parkingCount']}) (기대값: ₩29,700 / 총 7건 지출)")
        print(f"주유비 합계: {kpi_res['totalFuelFee']} ({kpi_res['fuelCount']}) (기대값: ₩270,000 / 총 3건 결제)")
        print(f"tripLogs 배열 건수: {kpi_res['tripLogsCount']}건")
        print(f"테이블 행 갯수: {kpi_res['rowsCount']}행")

        # Save Screenshot
        shot_path = os.path.join(artifact_dir, "wtt_801_october_72255_verified.png")
        page.screenshot(path=shot_path)
        print(f'\n[5] WTT 실측 스크린샷 저장 완료: {shot_path}')

        # Assertions
        assert '72,255' in kpi_res['prevMonthKm'], f"전월말 계기판 오류: {kpi_res['prevMonthKm']}"
        assert '73,865' in kpi_res['currentMonthKm'], f"당월말 계기판 오류: {kpi_res['currentMonthKm']}"
        assert '1,610' in kpi_res['totalDistanceKm'], f"총 주행거리 오류: {kpi_res['totalDistanceKm']}"
        assert '19' in kpi_res['operatingDays'], f"운행일수 오류: {kpi_res['operatingDays']}"
        assert '29,700' in kpi_res['totalParkingFee'], f"주차비 합계 오류: {kpi_res['totalParkingFee']}"
        assert '7' in kpi_res['parkingCount'], f"주차비 건수 오류: {kpi_res['parkingCount']}"
        assert '270,000' in kpi_res['totalFuelFee'], f"주유비 합계 오류: {kpi_res['totalFuelFee']}"
        assert '3' in kpi_res['fuelCount'], f"주유비 건수 오류: {kpi_res['fuelCount']}"
        assert kpi_res['tripLogsCount'] == 19, f"tripLogs 건수 오류: {kpi_res['tripLogsCount']}"

        print('\n>>> 모든 WTT 검증 및 지표 일치율 100% ALL PASS! <<<')
        browser.close()

if __name__ == '__main__':
    run_wtt()
