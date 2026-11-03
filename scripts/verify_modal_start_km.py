# -*- coding: utf-8 -*-
import sys, os
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

def verify_modal():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()

        print('[1] http://localhost:8080/vehicle_log_tracker.html 접속...')
        page.goto('http://localhost:8080/vehicle_log_tracker.html', wait_until='networkidle')
        page.wait_for_timeout(3000)

        print('[2] 801부8744 및 10월 선택...')
        page.evaluate('''() => {
            selectVehicle('801부8744');
            shiftMonth(-1);
        }''')
        page.wait_for_timeout(3000)

        print('[3] 운행종료 Km 자동 분배 모달 오픈...')
        page.evaluate('openAutoDistributeModal()')
        page.wait_for_timeout(2000)

        modal_data = page.evaluate('''() => {
            return {
                startKm: document.getElementById('autoStartKm').value,
                endKm: document.getElementById('autoEndKm').value,
                vehicleText: document.getElementById('autoDistributeVehicleText').innerText.trim(),
                monthText: document.getElementById('autoDistributeMonthText').innerText.trim(),
                driverText: document.getElementById('autoDistributeDriverText').innerText.trim()
            };
        }''')

        print(f"모달 시작 계기판: {modal_data['startKm']} (기대값: 72255)")
        print(f"모달 종료 계기판: {modal_data['endKm']}")
        print(f"차량: {modal_data['vehicleText']}")
        print(f"월: {modal_data['monthText']}")
        print(f"기사: {modal_data['driverText']}")

        assert str(modal_data['startKm']) == '72255', f"모달 startKm 불일치: {modal_data['startKm']}"
        print('>>> 자동 분배 모달 시작 계기판 72,255 일치 확인 PASS! <<<')
        browser.close()

if __name__ == '__main__':
    verify_modal()
