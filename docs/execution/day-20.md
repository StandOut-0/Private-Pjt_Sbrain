# Day 20 실행 보고서 — MVP 데모와 작업 인수 (최종 게이트 승인 아님)

아래의 원본 게이트 표와 테스트 수는 커밋 `2131a09` 당시의 결과 기록이다. 사후 보완 결과와 현재의 미충족 MVP 게이트는 이 문서 끝의 “사후 대조 기록”을 기준으로 본다.

## 완료 범위

- 프로젝트 생성 → 대화 저장 → Run 요청 → Planning Worker → Artifact 저장/다운로드 → Reflection 평가 → 프로젝트 상세 표시의 사용자 경로를 연결했다.
- 소유권, 멱등성, 재시도 횟수, 중단/재생성, 관리자 상태 조회 및 구조화된 오류를 검증했다.
- `front/README.md`에 로컬 서버/Worker 실행, React build, 데모 순서, API와 DB 앱, 미계측 데이터 의미를 추가했다.
- 일자별 구현·검증 보고서를 `docs/execution/README.md`에서 탐색할 수 있게 연결했다.

## 인수 게이트

| Gate | 결과 | 근거 |
| --- | --- | --- |
| DB schema/migration 동기화 | 통과 | `makemigrations --check --dry-run` 변경 없음 |
| Django system check | 통과 | `manage.py check` |
| Django 회귀/종단 간 테스트 | 통과 | 전체 53개 |
| React production build | 통과 | `npm run build` |
| Artifact/Reflection 소유권 | 통과 | 소유자 API 성공, 타 사용자 404 테스트 |
| React 화면 초기 데이터 연결 | 통과 | project detail payload 테스트 및 build |
| 브라우저 시각/실운영 인수 | 미실시 | 이 작업 세션은 브라우저 실화면 확인을 수행하지 않음 |
| Production readiness | 차단 | SQLite 전용, fake provider, worker supervisor/backup 자동화 없음 |

## 시연

실행 절차와 API 목록은 `front/README.md`의 “프로젝트 실행 MVP (Day 8–20)” 절을 따른다. 데모용 Planning과 Reflection은 mock이며 서비스 품질/비용을 나타내지 않는다.

## 후속 우선순위

1. 운영 DB 및 durable queue/worker supervisor로 전환하고 장애 복구를 검증한다.
2. HTTPS ingress, 운영 secrets, 백업·복구·보존 정책을 확정하고 운영 환경에서 권한/인수 테스트를 수행한다.
3. 실제 provider adapter를 별도 설계해 timeout, quota, spend cap, token/cost metering, 개인정보 마스킹을 구현한다.
4. Artifact 형식/다운로드 표시와 Reflection 화면을 사용자 요구에 맞춰 확장하고 브라우저 시각 QA를 수행한다.

## Git 상태

- Day별 기능과 보고서 커밋을 분리했다.
- 현재 작업은 로컬 `main` 브랜치에만 커밋했다. 원격 push는 수행하지 않았다.
- 기존 사용자 변경 `기획/4. 회의 - 아이디어 반영.txt`는 stage하거나 수정하지 않았다.

## 사후 대조 기록 (2026-10-26)

Day 20의 표는 당시 인수 점검 결과이며, 15-2의 필수 MVP 게이트 전부를 승인했다는 의미는 아니다. 후속 전체 점검 결과:

- 현재 Planning 기본 모델은 Fake에서 로컬 Ollama `gemma4:latest`로 변경했다. API key나 hosted inference 사용은 없으며 실제 Worker → PRD → Artifact 통합 테스트가 통과했다. Ollama·모델 설치와 실행은 로컬 Worker 컴퓨터에 필요하다.
- 전체 Django 회귀 테스트는 61개 발견, 60개 통과, opt-in Ollama live test 1개 생략이다. 해당 live test도 별도 실행해 통과했다. 상세 수치와 명령은 `기획/6. 테스트 및 보완.txt`에 기록한다.
- Reflection은 계속 규칙 기반 Mock 평가다. 기획안 15-2가 요구하는 “Mock 점수만으로 완료 처리하지 않음” 조건을 아직 충족하지 못했으므로 MVP 최종 수용은 **보류**다.
- 브라우저 시각/실제 사용자 수용 테스트는 여전히 미실시다. React 빌드와 Django 응답 기반 자동 검증을 브라우저 기능 동등성 검증으로 간주하지 않는다.
- Production readiness는 SQLite 동시성, durable worker/supervisor, 백업·복구/보존 자동화 미구성으로 계속 차단 상태다.
