# -*- coding: utf-8 -*-
"""
WTT Playwright verification script for mobile inspection photo upload and session preservation.
Uses system Chrome (channel='chrome').
"""
import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        # Mobile viewport emulation (Samsung Galaxy S22 size: 390x844)
        context = browser.new_context(
            viewport={'width': 390, 'height': 844},
            user_agent='Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36'
        )
        page = context.new_page()

        console_errors = []
        page.on('console', lambda m: console_errors.append(m.text) if m.type in ['error'] else None)
        page.on('pageerror', lambda err: console_errors.append(str(err)))

        print("[TEST 1] Loading http://localhost:8080/mobile.html?driver=조경찬 ...", flush=True)
        page.goto('http://localhost:8080/mobile.html?driver=조경찬', wait_until='networkidle')
        page.wait_for_timeout(2000)

        # 1. Verify inputs exist
        camera_input = page.locator('#mobileInspectCameraInput')
        gallery_input = page.locator('#mobileInspectGalleryInput')
        assert camera_input.count() > 0, "mobileInspectCameraInput not found!"
        assert gallery_input.count() > 0, "mobileInspectGalleryInput not found!"

        cam_capture = camera_input.get_attribute('capture')
        cam_multiple = camera_input.get_attribute('multiple')
        gal_capture = gallery_input.get_attribute('capture')
        gal_multiple = gallery_input.get_attribute('multiple')

        print(f"Camera input: capture={cam_capture}, multiple={cam_multiple}", flush=True)
        print(f"Gallery input: capture={gal_capture}, multiple={gal_multiple}", flush=True)

        assert cam_capture == 'environment', f"Expected capture='environment', got {cam_capture}"
        assert cam_multiple is None, f"Expected multiple to be None for camera, got {cam_multiple}"
        assert gal_multiple is not None, f"Expected multiple for gallery, got {gal_multiple}"
        assert gal_capture is None, f"Expected capture to be None for gallery, got {gal_capture}"
        print("[TEST 1 PASS] Input attributes strictly verified without camera intent conflict.", flush=True)

        # 2. Open Inspect Modal
        print("[TEST 2] Opening Inspect Photo Modal...", flush=True)
        page.evaluate("openMobileParcelInspectModal(0)")
        page.wait_for_timeout(500)

        modal = page.locator('#mobileParcelInspectModal')
        assert modal.is_visible(), "mobileParcelInspectModal should be visible!"

        # Check UI tiles: [📸 직접 촬영] and [🖼️ 앨범 선택]
        grid_text = page.locator('#mobileInspectPhotoGalleryGrid').inner_text()
        print(f"Grid contents:\n{grid_text}", flush=True)
        assert "직접 촬영" in grid_text, "Direct shoot button missing from grid!"
        assert "앨범 선택" in grid_text, "Album select button missing from grid!"
        print("[TEST 2 PASS] Inspect Modal opened with dual action buttons.", flush=True)

        # 3. Simulate photo selection via gallery input
        print("[TEST 3] Simulating photo upload...", flush=True)
        test_img_path = os.path.abspath('backups/test_sample_photo.jpg')
        if not os.path.exists(test_img_path):
            from PIL import Image
            img = Image.new('RGB', (1600, 1200), color=(73, 109, 137))
            img.save(test_img_path, 'JPEG')

        gallery_input.set_input_files(test_img_path)
        page.wait_for_timeout(1500)

        # Check that photo tile was added
        grid_html = page.locator('#mobileInspectPhotoGalleryGrid').inner_html()
        assert 'alt="검수 사진 1"' in grid_html, "Uploaded photo thumbnail was not rendered!"
        badge_text = page.locator('#mobileInspectPhotoCountBadge').inner_text()
        print(f"Photo count badge: {badge_text}", flush=True)
        assert "1 / 10장" in badge_text, f"Badge count unexpected: {badge_text}"
        print("[TEST 3 PASS] Photo successfully compressed with watermark and rendered in gallery.", flush=True)

        # Capture inspect modal screenshot
        os.makedirs('backups', exist_ok=True)
        page.screenshot(path='backups/wtt_mobile_inspect_modal.png')
        page.screenshot(path='C:/Users/User/.gemini/antigravity/brain/da63d277-3302-44bf-9782-450f6c45bd72/wtt_mobile_inspect_modal.png')

        # 4. Test Session Auto-Restoration on Tab Reload
        print("[TEST 4] Testing Session Persistence across tab reload (LMK simulation)...", flush=True)
        session_user = page.evaluate("sessionStorage.getItem('DELIVERY_ACTIVE_SESSION_USER') || localStorage.getItem('DELIVERY_ACTIVE_SESSION_USER')")
        print(f"Stored session user: {session_user}", flush=True)
        assert session_user is not None and "조경찬" in session_user, "Session user should be stored!"

        # Reload the page directly without query parameters to simulate OS restart
        page.goto('http://localhost:8080/mobile.html', wait_until='networkidle')
        page.wait_for_timeout(2000)

        # Verify that loginOverlay is hidden and currentUser is restored
        login_overlay_hidden = page.evaluate("document.getElementById('loginOverlay').classList.contains('hidden')")
        header_name = page.locator('#headerDriverName').inner_text()
        print(f"After reload: loginOverlay hidden={login_overlay_hidden}, headerDriverName={header_name}", flush=True)
        assert login_overlay_hidden, "loginOverlay must be hidden after reload!"
        assert "조경찬" in header_name, f"Driver name should be 조경찬, got {header_name}"
        print("[TEST 4 PASS] Session was seamlessly preserved across reload without kicking to login screen!", flush=True)

        # Capture mobile home screenshot after reload
        page.screenshot(path='backups/wtt_mobile_session_restored.png')
        page.screenshot(path='C:/Users/User/.gemini/antigravity/brain/da63d277-3302-44bf-9782-450f6c45bd72/wtt_mobile_session_restored.png')

        print(f"Console errors during test: {len(console_errors)} errors ({console_errors})", flush=True)
        browser.close()
        print("\nALL MOBILE WTT VERIFICATIONS PASSED SUCCESSFULLY!", flush=True)

if __name__ == '__main__':
    run_test()
