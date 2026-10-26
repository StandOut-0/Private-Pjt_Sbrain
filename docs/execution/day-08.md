# Day 8 — Run 요청과 멱등성

- 수행일: 2026-10-26
- 기준 문서: `기획/1. 기획안.txt` Day 8, Day 3 DBML, `docs/contracts/project-execution-api-v1.md`
- 상태: 완료 (Run 큐 등록·상태 조회·중복 요청 방지)

## 1. 수행 내용

- 실행 도메인을 `apps/execution`으로 분리하고 DBML의 `PROJECT_RUN` 기반 모델을 추가했다. Project, 요청 계정, Conversation, source User Message, 선택적 이전 Run, 상태, 피드백, instruction snapshot, 생성·시작·완료·중단시각을 저장한다.
- `(project_id, idempotency_key)` 고유 제약을 DB에 적용했다. 요청 키는 UUID 형식으로 검증하며, 동일 키와 동일 source message 재시도는 기존 Run을 반환하고 다른 source message에 재사용하면 `409 IDEMPOTENCY_KEY_REUSED`를 반환한다.
- `POST /api/v1/projects/{project_id}/runs/`는 Project·Conversation·Message 소유 관계를 서버에서 검사하고 `queued` 상태로 생성한다. Worker를 요청 처리 중 동기 실행하지 않는다.
- `GET /api/v1/projects/{project_id}/runs/{run_id}/`로 상태를 확인하고, 새 Run 생성 응답에는 `202 Accepted`와 `Location`을 반환한다.
- 프로젝트 상세의 채팅 제출은 Message 저장 뒤 UUID idempotency key로 Run을 요청한다. 기존 UI는 유지하고 아직은 queued만 저장한다. Task 분해와 실제 Planning은 Day 9–10 범위다.
- 모델을 `apps.projects`에 추가하지 않고 실행 앱으로 분리해 프로젝트 CRUD와 실행 lifecycle의 책임을 나눴다.

## 2. 검증 결과

| 검증 | 결과 |
| --- | --- |
| 전체 Django 테스트 | 33개 통과 |
| Run 생성 | `202`, `queued`, Location 확인 |
| 같은 source·같은 key 재시도 | `200`, 동일 Run ID, 중복 행 없음 |
| 같은 key·다른 source | `409 IDEMPOTENCY_KEY_REUSED` |
| 잘못된 UUID key | `422 VALIDATION_ERROR` |
| 다른 사용자 Project로 요청 | `404 PROJECT_NOT_FOUND` |
| Run 상태 조회 | 소유 사용자 `200`, DB 상태 `queued` 확인 |
| 실행 DB migration | `execution.0001_initial` 적용 완료 |
| Django check / migration drift | 통과 / 추가 migration 없음 |
| React production build | Vite 6.4.1, 1,647 modules 빌드 통과 |
| `git diff --check` | 통과 |

## 3. 검토 사항과 다음 단계

- Run은 현재 `queued`에 머문다. 실제 worker/queue를 붙이지 않은 상태에서 성공했다고 표시하지 않는다. Day 9에서 Run에서 Task를 생성하고 Day 10에서 fake Planning provider를 연결한다.
- Run 생성은 user role의 source Message만 허용한다. assistant 답변, 타 Conversation 메시지, 타 Project 소유 행은 source가 될 수 없다.
- 채팅 UI는 Run 응답을 별도 실행 Timeline으로 아직 표시하지 않는다. Day 14 서버 이벤트와 Timeline을 같은 원본으로 연결한다.
- 브라우저의 실제 viewport/screenshot 수동 검수는 수행하지 못했고, React build와 API/서버 테스트를 확인했다.

## 4. 변경 파일

- 실행 모델·migration/API: `front/apps/execution/`, `front/config/settings.py`, `front/apps/projects/api_urls.py`
- 채팅에서 Run 요청: `front/react/src/pages/AllPages.tsx` 및 빌드 산출물
- API 계약·회귀 테스트: `docs/contracts/project-execution-api-v1.md`, `front/apps/projects/tests.py`
