import os, sys, shutil, datetime

def apply_patch():
    base = r'c:\antigravity\배송스케줄관리'
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(base, 'backups', f'security_pipa_backup_{ts}')
    os.makedirs(backup_dir, exist_ok=True)
    print(f"Created backup directory: {backup_dir}")

    # Files to patch
    files = [
        'as_management.html',
        'asset_audit.html',
        'vehicle_log_tracker.html',
        'index.html',
        'mobile.html'
    ]

    for fname in files:
        fpath = os.path.join(base, fname)
        if not os.path.exists(fpath):
            print(f"File not found: {fname}")
            continue

        # Backup
        shutil.copy2(fpath, os.path.join(backup_dir, fname))
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 1. Patch as_management.html
        if fname == 'as_management.html':
            target = '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>'
            replacement = target + '\n<!-- 통합 보안 및 개인정보(PIPA) 가드 -->\n<script src="js/auth-guard.js?v=20261106"></script>\n<script>\n  document.addEventListener("DOMContentLoaded", function() {\n    if (window.AuthGuard) window.AuthGuard.ensurePageProtected({ pageName: "현대렌탈 A/S 및 거래처 인수인계 관리" });\n  });\n</script>'
            if 'js/auth-guard.js' not in content and target in content:
                content = content.replace(target, replacement, 1)
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"[OK] Patched {fname}")

        # 2. Patch asset_audit.html
        elif fname == 'asset_audit.html':
            target = '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>'
            replacement = target + '\n<!-- 통합 보안 및 개인정보(PIPA) 가드 -->\n<script src="js/auth-guard.js?v=20261106"></script>\n<script>\n  document.addEventListener("DOMContentLoaded", function() {\n    if (window.AuthGuard) window.AuthGuard.ensurePageProtected({ pageName: "스마트 바코드 자산 실사 및 누락 자동 검출" });\n  });\n</script>'
            if 'js/auth-guard.js' not in content and target in content:
                content = content.replace(target, replacement, 1)
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"[OK] Patched {fname}")

        # 3. Patch vehicle_log_tracker.html
        elif fname == 'vehicle_log_tracker.html':
            target = '<script src="js/supabase-config.js?v=20261103_v2"></script>'
            replacement = target + '\n<script src="js/auth-guard.js?v=20261106"></script>\n<script>\n  document.addEventListener("DOMContentLoaded", function() {\n    if (window.AuthGuard) window.AuthGuard.ensurePageProtected({ pageName: "현대렌탈 법인차량 운행일지 관리" });\n  });\n</script>'
            if 'js/auth-guard.js' not in content and target in content:
                content = content.replace(target, replacement, 1)
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"[OK] Patched {fname}")

        # 4. Patch index.html
        elif fname == 'index.html':
            target = '<script src="js/supabase-config.js"></script>'
            replacement = target + '\n<script src="js/auth-guard.js?v=20261106"></script>'
            if 'js/auth-guard.js' not in content and target in content:
                content = content.replace(target, replacement, 1)
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"[OK] Patched {fname}")

        # 5. Patch mobile.html
        elif fname == 'mobile.html':
            target = '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>'
            replacement = target + '\n<script src="js/auth-guard.js?v=20261106"></script>'
            if 'js/auth-guard.js' not in content and target in content:
                content = content.replace(target, replacement, 1)
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"[OK] Patched {fname}")

    print("Security & PIPA patch applied successfully to all target files.")

if __name__ == '__main__':
    apply_patch()
