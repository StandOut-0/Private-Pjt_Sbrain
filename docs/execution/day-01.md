# Day 1 — MVP 범위 고정 및 기준선 점검

- 수행일: 2026-10-20
- 기준 문서: `기획/1. 기획안.txt`의 15-2, 15-3, 16장
- 상태: 완료 (MVP 범위는 기획안 15-2를 기준으로 고정)

## 1. 오늘의 목표와 범위

기획안에는 20일 MVP 일정과 React 화면 전환 10일 일정이 함께 있다. React 화면 전환은 17장에 완료로 기록되어 있으므로 이번 실행은 16장의 **20일 MVP 일정**을 기준으로 진행한다. UI 전환 자체를 Backend 연결 완료로 간주하지 않는다.

MVP 시연 목표는 아래 한 흐름이다.

> 사용자 로그인 → 자기 프로젝트 생성 → 프로젝트 대화 저장 → 요청 실행 → Supervisor가 Planning 작업 생성 → Planning 결과를 Artifact 버전으로 저장 → Reflection 평가와 기준 snapshot 저장 → 진행·완료 상태와 결과 확인

동일 프로젝트·사용자 소유권, 중복 요청 방지, 실패·재시도 시 이전 결과 보존은 이 시연을 통과하기 위한 필수 조건이다. 현재 문서는 사용자가 적어 둔 15-2 범위를 Day 1 작업 기준으로 구체화한 것이며, 별도 확장 요구를 추가하지 않는다.

## 2. MVP 완료 체크리스트

- [ ] 개발 로그인 사용자와 Project 소유자를 서버에서 식별한다.
- [ ] 사용자가 생성한 Project가 DB에 저장되고, 소유자 기준으로 목록·상세가 조회된다.
- [ ] 타 사용자 Project 및 해당 대화·실행·파일에 접근할 수 없다.
- [ ] Project별 Conversation과 Message가 저장되고 새로고침 후에도 복원된다.
- [ ] 실행 요청은 Project와 사용자에 귀속되고, 같은 idempotency key의 중복 요청은 Run을 중복 생성하지 않는다.
- [ ] Supervisor 최소 경로가 요청을 구조화해 추적 가능한 Planning Task와 Execution을 만든다.
- [ ] Planning은 고정 입력·가짜 호출처로 재현 가능하고, 입력 오류와 실행 오류를 구조화한다.
- [ ] PRD 결과가 Project/Run/Task와 연결된 Artifact로 저장되고 재생성 시 새 버전이 추가된다.
- [ ] Reflection 결과에 점수·근거·감점·평가 당시 기준 snapshot이 연결된다.
- [ ] Run/Task/Execution 상태와 이벤트를 서버에 저장하고 화면이 실제 상태를 표시한다.
- [ ] 일시 실패는 설정된 상한 내에서만 재시도하며, 최종 실패가 이전 성공 Artifact를 덮어쓰지 않는다.
- [ ] 일반 사용자·관리자 권한 경계, 빈 상태·실패 상태, 직접 URL 진입을 확인한다.
- [ ] 브라우저에서 새 프로젝트부터 최종 결과 확인까지 한 번의 데모를 수행하고, 검증 기록을 남긴다.

완료 판정은 모든 필수 항목을 시연과 서버 검증으로 확인했을 때만 한다. 화면의 샘플 데이터, 고정 수치, Stub 응답은 완료 증거로 세지 않는다.

## 3. MVP 제외 범위

기획안 15-2를 따라 아래는 MVP 필수 게이트에서 제외한다.

- Creative, Engineering, Data, AI 등 Planning 이외 Worker의 확장 실행
- 고급 RAG·Memory, MCP·A2A
- 실제 Google OAuth 및 관리자 Face 인증
- 실제 메일 초대 발송
- 고급 Safety Filter와 범용 전역 검색
- 자동 배포

제외는 보안·권한 기본 검증, 실행 오류 처리, 결과 보존을 생략한다는 뜻이 아니다. 필수 시나리오 완료 후 일정이 남을 때만 후보 기능을 검토한다.

## 4. 작업 단위

Day 1 범위는 기획안의 기존 20일 순서를 따르며, 이슈 추적은 저장소 안의 작은 작업 단위와 커밋으로 남긴다. Jira 연동이나 외부 이슈 생성은 하지 않았다.

| 작업 단위 | 일자 | 산출물 / 게이트 |
| --- | --- | --- |
| 구성·환경 경계 | Day 2 | Django / React / Agent 책임, 환경변수·비밀값 표 |
| 데이터 계약 | Day 3 | User·Project·Conversation·Message·Run 데이터 흐름과 DBML 검토 |
| API 계약 | Day 4 | 생성·대화·실행·상태·Artifact 계약과 오류 예시 |
| DB·소유권·저장 | Day 5–7 | 마이그레이션, Project 저장/권한, 새로고침 후 대화 복원 |
| 실행 요청·Supervisor | Day 8–9 | 멱등 Run 생성, 추적 가능한 Planning Task |
| Planning·Artifact·Reflection | Day 10–13 | 재현 가능한 PRD, 버전 보존, 평가 snapshot |
| 이벤트·실패·취소 | Day 14–16 | 상태 Timeline, 제한 재시도, 취소·재생성 규칙 |
| 관리자 관측·보안 | Day 17–18 | 실행/사용량 관측, 권한·파일·비밀값·운영 점검 |
| E2E·인수 | Day 19–20 | 시연 기록, 미해결 결함, README와 인수 체크리스트 |

## 5. 기존 구현 기준선

| 영역 | 현재 확인된 상태 | MVP 영향 / 후속 게이트 |
| --- | --- | --- |
| Django / React | Django URL·세션·페이지별 초기 JSON과 React 화면이 연결되어 있다. | Backend 데이터 연결은 별도로 완료해야 한다. |
| Project | `apps/projects/views.py`가 `apps.mockdata`를 읽고 생성도 임시 데이터에 기록한다. `apps/projects/models.py`에는 모델이 없다. | Day 5–6에 실제 저장·소유권을 연결한다. |
| Chat | 프로젝트 Chat 응답은 Supervisor 안내 문구를 돌려주는 Stub이다. | Day 7에 Message 저장, Day 8–10에 실행 계약과 Planning 연결. |
| 상세 권한 | 로그인 검사는 있으나 Project 상세에서 사용자 소유권을 검증하는 저장 계층이 아직 없다. | Day 5 소유권 게이트에서 구현·검증한다. |
| Agent / Tasks / Results | 관리자 화면 데이터는 `apps.mockdata`에 기반한다. | MVP의 단일 Planning 경로와 화면의 Mock 상태 표시를 구분한다. |
| Coming Soon | 별도의 Markdown 파일 저장 흐름이 구현되어 있다. | 핵심 실행 흐름과 독립 기능이므로 MVP 완료 게이트에서 제외한다. |
| 환경·운영 | Django 설정과 로컬 DB가 있으나 환경별 비밀값·운영값 검토는 남아 있다. | Day 2에서 `.env.example`과 설정 경계를 확인한다. |

## 6. 비슷한 Sbrain 프로젝트에서 참고한 점

`C:\Users\playdata2\Desktop\Sbrain`은 FastAPI·React 기반의 별도 프로젝트다. 그대로 옮기지 않고 다음 설계 패턴만 참고한다.

- API 테스트에서 사용자별 데이터 격리, 잘못된 입력, 중복·동시 실행, 재시도 경계를 구분해 검증한다.
- 비동기 작업 상태를 프로세스 메모리에만 두지 않고 재시작 뒤에도 복구 가능한 저장 경계에 둔다. 해당 프로젝트의 DB claim 구현은 현재 Django 모델·실행 계약을 확인한 뒤 필요할 때만 참고한다.
- 로컬 실행과 환경값을 README 및 `.env.example`로 명시하고, 외부 서비스 없는 기본 검증을 둔다.

현재 저장소는 Django 세션과 URL 구조를 유지해야 하므로 FastAPI 라우터, SQLAlchemy 모델, 인증 코드를 복사하지 않았다. Day 1에서는 재사용 코드보다 적용할 원칙을 식별하는 것이 범위에 맞다.

## 7. Day 1 검증 결과

| 검증 | 결과 |
| --- | --- |
| `front/.venv/Scripts/python.exe manage.py check` | 통과, 시스템 체크 이슈 없음 |
| `front/.venv/Scripts/python.exe manage.py test apps` | 수정 후 15개 통과 |
| `front/react`의 `npm run build` | 통과, Vite production bundle 생성 |
| 로컬 Django `/login/` HTTP 확인 | 200 |
| 브라우저 시각 회귀 확인 | 미완료. Computer Use 브라우저 런타임 초기화가 `지정된 경로를 찾을 수 없습니다`로 실패해 실제 캡처·화면 크기별 확인은 하지 못함 |

테스트 실패 1건은 구현 오류가 아니라 테스트 기대값이 팝업 설계와 어긋난 문제였다. 새 프로젝트 GET 경로는 팝업이 있는 프로젝트 목록으로 redirect하도록 이미 구현되어 있었으나 `SmokeTest.test_user_pages`가 200을 기대했다. 테스트를 별도 redirect 검증으로 교체한 뒤 전체 15개가 통과했다. 사용자 화면이나 인증 동작은 변경하지 않았다.

### 확인한 URL / 권한 기준

| URL | 권한 | 현재 기준선 |
| --- | --- | --- |
| `/`, `/projects/list/` | 로그인 사용자 | React 화면, Mock 데이터 |
| `/projects/create/` | 로그인 사용자 | GET은 목록으로 이동, POST 생성은 현재 Mock |
| `/projects/<id>/`, `/projects/<id>/chat/` | 로그인 사용자 | Mock 상세 / Chat Stub, 소유권 저장 검증 미구현 |
| `/manage/tasks/`, `/manage/agents/`, `/manage/results/` | 관리자 | 서버 `admin_required`, Mock 데이터 |
| `/notifications/` | 로그인 사용자 | React 화면, Mock 알림 |
| `/login/`, `/login/demo/`, `/login/face/` | 공개 진입 | 임시 세션 로그인 흐름 |

## 8. 발견 사항 및 다음 작업

1. 기존 테스트의 `/projects/create/` 기대값을 팝업 진입 설계와 일치시켰다. 상세 변경은 `[accounts/tests.py](../../front/apps/accounts/tests.py)`에 있다.
2. 제품 UI의 브라우저 캡처 검수는 런타임 문제로 미완료다. 다음 화면 검수 가능한 환경에서 Dashboard·프로젝트 목록·새 프로젝트 팝업을 데스크톱/모바일로 확인한다.
3. MVP 기능의 현재 화면 경로는 Mock/Stub 상태다. 다음 구현 전제는 Day 2 환경·책임 경계 정리와 Day 3 데이터 계약이다.
4. 사용자 회의 메모 파일의 기존 수정은 Day 1 작업과 무관하므로 변경하거나 포함하지 않았다.

## 9. 커밋 경계

- `[FIX] 프로젝트 생성 팝업 흐름에 맞춰 테스트 수정` — stale SmokeTest 기대값 보정
- `[DOCS] Day 1 MVP 범위 및 기준선 보고서 추가` — 본 보고서와 기획 일정의 실행 기록 연결

두 커밋 모두 로컬에만 기록하고 원격으로 push하지 않는다.
