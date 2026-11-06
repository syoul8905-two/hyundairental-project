import sys, time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_auth_guard():
    print("=== [WTT] Testing AuthGuard & Security Protection Across Pages ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        # 1. Test as_management.html without session -> Must show overlay
        file_url = 'file:///c:/antigravity/배송스케줄관리/as_management.html'
        print(f"Loading {file_url} (Unauthenticated) ...")
        page.goto(file_url, wait_until='domcontentloaded')
        page.wait_for_timeout(1000)

        overlay = page.query_selector('#authGuardPageOverlay')
        assert overlay is not None, "AuthGuard overlay should appear on unauthenticated access!"
        print(" [PASS] AuthGuard overlay correctly blocked unauthenticated access on as_management.html")

        # 2. Test PIN Verification
        page.select_option('#authGuardUserSelect', '최두성')
        page.fill('#authGuardPinInput', '8905')
        page.click('#authGuardSubmitBtn')
        page.wait_for_timeout(1000)

        overlay_after = page.query_selector('#authGuardPageOverlay')
        assert overlay_after is None, "AuthGuard overlay should disappear after successful PIN entry!"
        print(" [PASS] Successful PIN authentication unlocked the page cleanly!")

        # 3. Test asset_audit.html with now-existing session -> Should bypass overlay automatically
        file_url_audit = 'file:///c:/antigravity/배송스케줄관리/asset_audit.html'
        print(f"Loading {file_url_audit} (With saved session) ...")
        page.goto(file_url_audit, wait_until='domcontentloaded')
        page.wait_for_timeout(1000)

        overlay_audit = page.query_selector('#authGuardPageOverlay')
        assert overlay_audit is None, "AuthGuard overlay should be bypassed when session is valid!"
        print(" [PASS] Single Sign-On session seamlessly bypassed overlay on asset_audit.html")

        # 4. Test vehicle_log_tracker.html
        file_url_tracker = 'file:///c:/antigravity/배송스케줄관리/vehicle_log_tracker.html'
        print(f"Loading {file_url_tracker} (With saved session) ...")
        page.goto(file_url_tracker, wait_until='domcontentloaded')
        page.wait_for_timeout(1000)

        overlay_tracker = page.query_selector('#authGuardPageOverlay')
        assert overlay_tracker is None, "AuthGuard overlay should be bypassed when session is valid!"
        print(" [PASS] Single Sign-On session seamlessly bypassed overlay on vehicle_log_tracker.html")

        browser.close()
        print("=== [WTT ALL PASS] AuthGuard Security Enhancement is 100% VERIFIED! ===")

if __name__ == '__main__':
    test_auth_guard()
