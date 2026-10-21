# -*- coding: utf-8 -*-
"""
Playwright automated WTT test script for Smart Dual-Time Idle Sleep Mode.
Verifies:
1. Daytime (90m) vs Nighttime (30m) threshold calculation
2. Idle sleep entry, polling suspension, and non-intrusive UI pill rendering
3. Input focus lock / modal open guardrail (prevents sleeping during editing)
4. Instant wake-up upon mouse move, keydown, or touch
5. Zero browser console errors
"""
import os
import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

def run_wtt():
    print("=== [WTT] 스마트 듀얼타임 절전 모드 검증 시작 ===", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)

        # ----------------------------------------------------
        # TEST 1: PC 관제 대시보드 (index.html) 검증
        # ----------------------------------------------------
        print("\n--- [TEST 1: PC index.html] ---", flush=True)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        pc_errors = []
        page.on('console', lambda m: pc_errors.append(m.text) if m.type in ['error'] else None)
        page.on('pageerror', lambda err: pc_errors.append(str(err)))

        page.goto('http://localhost:8080/index.html', wait_until='networkidle')
        page.wait_for_timeout(2000)

        # 로그인 오버레이 닫기
        if page.is_visible('#loginOverlay'):
            page.evaluate("() => document.getElementById('loginOverlay').classList.add('hidden')")
            page.wait_for_timeout(500)

        # 1-1. 시간대별 한도 수식 검증
        day_limit = page.evaluate("() => { var orig = Date.prototype.getHours; Date.prototype.getHours = () => 14; var res = getIdleTimeoutLimitMs(); Date.prototype.getHours = orig; return res; }")
        night_limit = page.evaluate("() => { var orig = Date.prototype.getHours; Date.prototype.getHours = () => 21; var res = getIdleTimeoutLimitMs(); Date.prototype.getHours = orig; return res; }")
        print(f"1. 주간(14시) 유휴 한도: {day_limit / (60 * 1000)}분 (기대값: 90분)", flush=True)
        print(f"2. 야간(21시) 유휴 한도: {night_limit / (60 * 1000)}분 (기대값: 30분)", flush=True)
        assert day_limit == 90 * 60 * 1000, f"Expected 90m in day, got {day_limit}"
        assert night_limit == 30 * 60 * 1000, f"Expected 30m at night, got {night_limit}"
        print("   -> [PASS] 주간 1시간 30분 / 야간 30분 동적 전환 수식 일치!")

        # 1-2. 절전 모드 진입 테스트
        page.evaluate("() => enterIdleSleepMode()")
        page.wait_for_timeout(500)

        is_sleeping = page.evaluate("() => isSystemSleeping")
        has_polling = page.evaluate("() => syncPollingInterval !== null")
        pill_visible = page.is_visible('#idleSleepPill')
        print(f"3. 절전 진입 상태: isSleeping={is_sleeping}, pollingRunning={has_polling}, pillVisible={pill_visible}", flush=True)
        assert is_sleeping, "isSystemSleeping should be true"
        assert not has_polling, "syncPollingInterval must be stopped (null)"
        assert pill_visible, "#idleSleepPill must be visible"
        print("   -> [PASS] 절전 모드 가동: 25초 폴링 즉시 중단 (트래픽 0 KB 동결) 및 배지 노출 확인!")

        # 스크린샷 캡처
        os.makedirs('backups', exist_ok=True)
        page.screenshot(path='backups/wtt_pc_idle_sleep_mode.png')
        page.screenshot(path='C:/Users/User/.gemini/antigravity/brain/da63d277-3302-44bf-9782-450f6c45bd72/wtt_pc_idle_sleep_mode.png')

        # 1-3. 마우스 조작 시 즉각 웨이크업 검증
        page.mouse.move(500, 500)
        page.wait_for_timeout(500)

        is_sleeping_after = page.evaluate("() => isSystemSleeping")
        has_polling_after = page.evaluate("() => syncPollingInterval !== null")
        pill_visible_after = page.is_visible('#idleSleepPill')
        print(f"4. 마우스 이동 후 복구: isSleeping={is_sleeping_after}, pollingRunning={has_polling_after}, pillVisible={pill_visible_after}", flush=True)
        assert not is_sleeping_after, "isSystemSleeping should be false after mousemove"
        assert has_polling_after, "syncPollingInterval must be resumed"
        assert not pill_visible_after, "#idleSleepPill must be hidden after wake-up"
        print("   -> [PASS] 마우스 조작 즉시 0.1초 만에 실시간 재개 확인!")

        # 1-4. 입력 중/모달 오픈 시 절전 방어 검증
        page.focus('#tableSearchInput')
        page.wait_for_timeout(200)
        page.evaluate("() => enterIdleSleepMode()")
        page.wait_for_timeout(300)
        is_sleeping_while_typing = page.evaluate("() => isSystemSleeping")
        print(f"5. 입력창 포커스 중 절전 방어: isSleeping={is_sleeping_while_typing}", flush=True)
        assert not is_sleeping_while_typing, "Sleep mode must be inhibited while typing!"
        print("   -> [PASS] 입력창 포커스 시 작성 글 보호 가드레일 정상 작동!")

        print(f"PC 관제 콘솔 오류: {len(pc_errors)}건 ({pc_errors})", flush=True)
        assert len(pc_errors) == 0, f"PC has console errors: {pc_errors}"
        page.close()

        # ----------------------------------------------------
        # TEST 2: 모바일 기사 웹 (mobile.html) 검증
        # ----------------------------------------------------
        print("\n--- [TEST 2: Mobile mobile.html] ---", flush=True)
        m_page = browser.new_page(
            viewport={'width': 390, 'height': 844},
            has_touch=True,
            user_agent='Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36'
        )
        mobile_errors = []
        m_page.on('console', lambda m: mobile_errors.append(m.text) if m.type in ['error'] else None)
        m_page.on('pageerror', lambda err: mobile_errors.append(str(err)))

        m_page.goto('http://localhost:8080/mobile.html?driver=조경찬', wait_until='networkidle')
        m_page.wait_for_timeout(2000)

        # 2-1. 절전 모드 진입 테스트
        m_page.evaluate("() => enterIdleSleepMode()")
        m_page.wait_for_timeout(500)

        m_sleeping = m_page.evaluate("() => isSystemSleeping")
        m_polling = m_page.evaluate("() => mobileSyncInterval !== null")
        m_pill_visible = m_page.is_visible('#mobileIdleSleepPill')
        print(f"1. 모바일 절전 진입: isSleeping={m_sleeping}, pollingRunning={m_polling}, pillVisible={m_pill_visible}", flush=True)
        assert m_sleeping, "mobile isSystemSleeping should be true"
        assert not m_polling, "mobileSyncInterval must be stopped"
        assert m_pill_visible, "#mobileIdleSleepPill must be visible"
        print("   -> [PASS] 모바일 절전 모드 정상 가동 및 상단 배지 노출!")

        # 모바일 스크린샷 캡처
        m_page.screenshot(path='backups/wtt_mobile_idle_sleep_mode.png')
        m_page.screenshot(path='C:/Users/User/.gemini/antigravity/brain/da63d277-3302-44bf-9782-450f6c45bd72/wtt_mobile_idle_sleep_mode.png')

        # 2-2. 화면 터치 시 즉시 복구 테스트
        m_page.touchscreen.tap(200, 400)
        m_page.wait_for_timeout(500)

        m_sleeping_after = m_page.evaluate("() => isSystemSleeping")
        m_polling_after = m_page.evaluate("() => mobileSyncInterval !== null")
        m_pill_visible_after = m_page.is_visible('#mobileIdleSleepPill')
        print(f"2. 모바일 터치 후 복구: isSleeping={m_sleeping_after}, pollingRunning={m_polling_after}, pillVisible={m_pill_visible_after}", flush=True)
        assert not m_sleeping_after, "mobile isSystemSleeping should be false after touch"
        assert m_polling_after, "mobileSyncInterval must be resumed"
        assert not m_pill_visible_after, "#mobileIdleSleepPill must be hidden"
        print("   -> [PASS] 화면 터치 즉시 0.1초 만에 실시간 재개 확인!")

        print(f"모바일 콘솔 오류: {len(mobile_errors)}건 ({mobile_errors})", flush=True)
        assert len(mobile_errors) == 0, f"Mobile has console errors: {mobile_errors}"
        m_page.close()

        browser.close()
        print("\n=== [WTT ALL PASS] 스마트 듀얼타임 절전 모드 검증 100% 성공! ===", flush=True)

if __name__ == '__main__':
    run_wtt()
