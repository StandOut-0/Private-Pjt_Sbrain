# Day 9 — Supervisor 최소 경로

- 수행일: 2026-10-26
- 기준 문서: `기획/1. 기획안.txt` Day 9, Day 3 DBML, API 계약
- 상태: 완료 (사용자 요청 → Run → Planning Task)

## 1. 수행 내용

- `apps.execution.Task` 모델을 추가하고 Project 및 ProjectRun과 연결했다. 한 Run에는 `OneToOne` 제약으로 Planning Task를 최대 하나만 둔다.
- `apps.execution.supervisor.structure_request()`는 입력 원문을 보존하면서 request type, 목표, 알려진 요구사항, 다음 Agent, 예상 산출물, Task 제목으로 구조화한다. 로고·설문·원페이지 입력은 간단한 분류를 수행하고 그 외는 일반 PRD 요청으로 분류한다.
- Run 생성과 같은 DB 트랜잭션에서 instruction snapshot을 기록하고 `queued` Planning Task를 만든다. 중복 API 재시도와 동시 unique 충돌 경로는 `get_or_create`로 기존 Task를 반환한다.
- Run 상태 응답에 연결 Task의 `id/title/status`를 포함했다. Day 8 이전 생성된 queued Run은 상태 조회 시 Task가 없으면 한 번 생성해 기존 데이터도 연결한다.
- 기능을 실제 LLM 호출 또는 Agent 실행으로 표현하지 않는다. 이 단계의 Supervisor 분해는 규칙 기반이며 Planning 실행은 다음 Day 10에서 다룬다.

## 2. 검증 결과

| 검증 | 결과 |
| --- | --- |
| 전체 Django 테스트 | 33개 통과 |
| Run → instruction snapshot → Planning Task | `queued` Run과 Task, `next_agent=planning` 확인 |
| 같은 idempotency 요청 재시도 | Task 포함 기존 Run 응답, Task 중복 없음 |
| user가 아닌 assistant source message | `404 MESSAGE_NOT_FOUND` |
| 타 사용자 Project / Run | 404로 숨김 |
| `execution.0002_task` migration | 개발 DB 적용 완료 |
| Django check / migration drift | 통과 / 추가 migration 없음 |
| `git diff --check` | 통과 |

## 3. 구조 점검

- ProjectRun과 Task가 같은 트랜잭션 경계에서 생성돼 Run만 있고 Task가 빠진 반쪽 실행이 생기지 않는다.
- Task unique 관계가 Supervisor 중복 호출을 방어한다. 다음 단계의 여러 Agent Task 분해가 필요해지면 OneToOne을 일반 FK와 `(run, agent/ordinal)` unique로 확장해야 한다. 현재는 계획대로 최소 Planning Task 하나만 생성한다.
- 실제 브라우저 screenshot 검수는 하지 않았다. 이 Day는 백엔드 변화이며 전체 Django 테스트로 API 흐름을 검증했다.

## 4. 변경 파일

- 모델·migration·구조화: `front/apps/execution/models.py`, `supervisor.py`, `migrations/0002_task.py`
- Run 생성 경로: `front/apps/execution/api.py`
- 테스트·계약: `front/apps/projects/tests.py`, `docs/contracts/project-execution-api-v1.md`
