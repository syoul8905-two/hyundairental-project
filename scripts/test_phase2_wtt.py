# -*- coding: utf-8 -*-
import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def run_tests():
    print("=== [WTT] Phase 2 Security, Passcode Masking & Audit WTT ===", flush=True)
    all_passed = True
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        # 1. Test index.html with AuthGuard Phase 2
        file_url_index = "file:///c:/antigravity/배송스케줄관리/index.html"
        print(f"Loading {file_url_index} ...", flush=True)
        page.goto(file_url_index, wait_until='domcontentloaded')
        page.wait_for_timeout(1000)

        # Check AuthGuard exports
        has_guard = page.evaluate("""() => {
            return !!(window.AuthGuard && 
                      typeof window.AuthGuard.maskSensitivePasscodes === 'function' &&
                      typeof window.AuthGuard.recordPrivacyAudit === 'function' &&
                      typeof window.AuthGuard.hasPasscode === 'function');
        }""")
        print(f"  ▶ AuthGuard & recordPrivacyAudit exists in index.html: {has_guard}", flush=True)
        assert has_guard, "AuthGuard methods missing in index.html"

        # Check passcode masking output
        masked_html = page.evaluate("""() => {
            return window.AuthGuard.maskSensitivePasscodes('경비실 호출 후 공동현관 #8905# 눌러주세요');
        }""")
        print(f"  ▶ Masked HTML sample: {masked_html}", flush=True)
        assert '••••' in masked_html and '열람' in masked_html and '#8905#' not in masked_html, "Passcode masking failed!"

        # Check hasPasscode
        assert page.evaluate("() => window.AuthGuard.hasPasscode('공동현관 #1234#')") == True
        assert page.evaluate("() => window.AuthGuard.hasPasscode('문앞에 놓아주세요')") == False
        print("  ▶ hasPasscode logic: PASS", flush=True)

        # 2. Test mobile.html with AuthGuard Phase 2
        file_url_mobile = "file:///c:/antigravity/배송스케줄관리/mobile.html"
        print(f"Loading {file_url_mobile} ...", flush=True)
        mobile_page = context.new_page()
        mobile_page.goto(file_url_mobile, wait_until='domcontentloaded')
        mobile_page.wait_for_timeout(1000)

        has_mobile_guard = mobile_page.evaluate("""() => {
            return !!(window.AuthGuard && typeof window.AuthGuard.maskSensitivePasscodes === 'function');
        }""")
        print(f"  ▶ AuthGuard & maskSensitivePasscodes exists in mobile.html: {has_mobile_guard}", flush=True)
        assert has_mobile_guard, "AuthGuard missing in mobile.html"

        # Test interactive togglePasscode in DOM
        toggle_test = mobile_page.evaluate("""() => {
            const div = document.createElement('div');
            div.innerHTML = window.AuthGuard.maskSensitivePasscodes('비번: #4321#');
            document.body.appendChild(div);
            const span = div.querySelector('span');
            const beforeText = span.innerText;
            window.AuthGuard.togglePasscode(span, encodeURIComponent('#4321#'));
            const afterText = span.innerText;
            window.AuthGuard.togglePasscode(span, encodeURIComponent('#4321#'));
            const revertText = span.innerText;
            div.remove();
            return { before: beforeText, after: afterText, revert: revertText };
        }""")
        print(f"  ▶ Interactive toggle result: {toggle_test}", flush=True)
        assert '4321' in toggle_test['after'] and '숨김' in toggle_test['after'], "Toggle reveal failed!"
        assert '••••' in toggle_test['revert'] and '열람' in toggle_test['revert'], "Toggle revert failed!"

        browser.close()
        print("\n🎉 [ALL WTT TESTS PASSED] Phase 2 Security & PIPA Passcode Masking verified 100%!", flush=True)

    return all_passed

if __name__ == '__main__':
    ok = run_tests()
    sys.exit(0 if ok else 1)
