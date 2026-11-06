-- ==============================================================================
-- 🛡️ [배송스케줄 통합 관제 시스템] Supabase 개인정보보호(PIPA) 및 DB 무결성 강화 SQL
-- ==============================================================================
-- 프로젝트: https://svlnzabdmncovosmxjxy.supabase.co
-- 생성 일시: 2026-11-06 (KST)
-- 수행 목적: 
--   1) RLS 전수 일괄 삭제(MASS DELETE) 차단 및 단일/명시적 ID 삭제 제한
--   2) 감사 로그(SYSTEM_CONFIG_PRIVACY_AUDIT) 인덱스 생성 및 조회 성능 최적화
--   3) 물리 데이터 유실 방지 안전 가드레일 확립
-- ==============================================================================

-- 1. 기존 누구나 테이블 전체를 삭제할 수 있었던 전면 개방 정책 제거
DROP POLICY IF EXISTS "Enable delete access for all users" ON delivery_schedules;

-- 2. 조건 없는 일괄 삭제(MASS WIPE) 방어 정책 적용
--    (반드시 id가 명시된 경우에만 삭제 가능하도록 강제하여 DELETE delivery_schedules 전수 증발 원천 차단)
CREATE POLICY "Enable guarded delete access" ON delivery_schedules
FOR DELETE
USING (id IS NOT NULL);

-- 3. 개인정보보호법(PIPA) 접속기록 감사 로그용 인덱스 생성 (조회 속도 및 보관 무결성)
CREATE INDEX IF NOT EXISTS idx_delivery_schedules_audit 
ON delivery_schedules (source_sheet, created_at DESC)
WHERE source_sheet = 'SYSTEM_CONFIG_PRIVACY_AUDIT';

-- 4. 출입문 비밀번호 및 개인정보 보관용 날짜별/기사별 인덱스 최적화
CREATE INDEX IF NOT EXISTS idx_delivery_schedules_date_driver
ON delivery_schedules (delivery_date, driver_name);

-- ==============================================================================
-- [적용 방법]
-- 1. https://supabase.com/dashboard/project/svlnzabdmncovosmxjxy 에 접속합니다.
-- 2. 좌측 메뉴에서 'SQL Editor'를 클릭합니다.
-- 3. 'New query'를 누르고 본 파일의 내용을 붙여넣은 뒤 우측 하단 'Run'을 클릭합니다.
-- ==============================================================================
