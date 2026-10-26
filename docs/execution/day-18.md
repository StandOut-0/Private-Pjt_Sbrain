# Day 18 실행 보고서 — 보안·운영 점검

## 보완

- project/execution JSON API의 request body를 64 KiB로 제한하고 초과 시 구조화된 413 응답을 반환한다.
- 다운로드 응답의 MIME type을 JSON으로 고정하고 `nosniff` 헤더와 owner/project 관계 검증을 확인했다.
- 운영 모드에서 secure session/CSRF cookie, content sniffing/referrer 정책을 켠다. Django 기본 CSRF middleware는 모든 요청에 적용된다.
- 예외 stack과 원문이 로그에 남지 않도록 Planning 예외 로깅을 식별자·예외 유형만 기록하게 바꿨다.
- 운영 필수 선행조건과 미구현 운영 항목을 `docs/operations/security-checklist.md`에 기록했다.

## 검증

- `manage.py test`: 전체 52개 통과. 소유권 경계, 안전한 다운로드 header, oversized JSON rejection 및 기존 실행 시나리오를 확인했다.
- `manage.py check`: 이상 없음.
- `manage.py makemigrations --check --dry-run`: 변경 없음.
- 소스 점검에서 실행 DB 설정은 SQLite 전용으로 확인했다. 이는 운영 배포 전 PostgreSQL 등 동시성 지원 DB로 바꾸어야 하는 제한으로 체크리스트에 남겼다.

## 남은 운영 위험

- 실 provider/실제 timeout, 다중 worker용 DB queue, 백업·복구·보존 자동화와 모니터링은 아직 구성하지 않았다. 이 저장소의 현재 상태만으로 운영 배포를 선언할 수 없다.
