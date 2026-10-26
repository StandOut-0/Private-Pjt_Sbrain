# Project Execution API v1 — 계약 초안

- 상태: Project 흐름은 Day 6, Conversation·Message 흐름은 Day 7, Run·멱등성은 Day 8, Supervisor Task는 Day 9, fake Planning 실행은 Day 10, DB Artifact와 소유권 API는 Day 11, 품질 기준과 mock Reflection은 Day 12~13, 공통 실행 이벤트는 Day 14, 실패 지점 재시도는 Day 15, 중단·재생성은 Day 16, DB 기반 관리자 실행 관측은 Day 17 구현 완료.
- 기반: Django 세션 인증, 기존 프로젝트 URL과 DBML 핵심 실행 경로
- 범위: Project 생성·조회, Conversation·Message 저장, Run 요청·상태 조회, Artifact 조회·다운로드

## 공통 규칙

- API prefix는 `/api/v1`이다. 기존 페이지 URL(`/projects/...`)은 Django 화면 호환 경로로 유지한다.
- 인증은 Django 세션 쿠키로 수행한다. 상태 변경 `POST`는 same-origin 요청과 `X-CSRFToken` 헤더를 사용한다.
- API 인증 실패는 HTML 로그인 redirect 대신 JSON `401`을 반환한다. 일반 페이지 redirect 동작은 바꾸지 않는다.
- 요청·응답은 JSON이며 시간은 UTC ISO-8601(`Z`) 형식이다. 응답에 서버 경로, 파일 시스템 경로, 비밀값은 노출하지 않는다.
- 클라이언트는 `user_id`, `requested_by`, role, 소유자 ID를 보내지 않는다. 서버 세션에서 사용자 ID를 결정한다.
- 인증은 되었지만 리소스가 없거나 다른 사용자의 소유면 동일하게 `404`를 반환해 존재 여부를 숨긴다.
- 생성·변경은 서버 권한 검증과 같은 DB 트랜잭션 경계에서 처리한다.

## 자원과 규칙

### 1. Project 목록

`GET /api/v1/projects/?query={text}&status={status}&limit=25&cursor={opaque}`

`200 OK`

```json
{
  "items": [
    {
      "id": 41,
      "title": "반려동물 용품 쇼핑몰",
      "summary": "반려동물 용품을 판매하는 온라인 스토어",
      "status": "active",
      "created_at": "2026-10-20T03:10:00Z",
      "updated_at": "2026-10-20T03:10:00Z"
    }
  ],
  "next_cursor": null
}
```

목록은 로그인 사용자의 Project만 반환한다. 정렬은 `updated_at DESC, id DESC`. 기본 페이지 크기는 25, 최대 100이다. 잘못된 상태 필터는 `422 VALIDATION_ERROR`로 거부한다.

### 2. Project 생성

`POST /api/v1/projects/`

```json
{
  "title": "반려동물 용품 쇼핑몰",
  "summary": "반려동물 용품을 판매하는 온라인 스토어",
  "initial_message": "반려동물 보호자를 위한 쇼핑몰을 기획해줘."
}
```

`title`은 trim 후 2–80자 필수, `summary`는 최대 500자, `initial_message`는 생략 가능하며 지정하면 trim 후 1–10,000자다. `initial_message`가 있으면 Project·기본 Conversation·사용자 Message를 한 트랜잭션에서 생성한다. `goal` UI 필드는 이 `initial_message`로 매핑한다. 여기서는 Agent 실행을 시작하지 않는다.

`201 Created`

```json
{
  "project": {
    "id": 41,
    "title": "반려동물 용품 쇼핑몰",
    "summary": "반려동물 용품을 판매하는 온라인 스토어",
    "status": "active",
    "created_at": "2026-10-20T03:10:00Z",
    "updated_at": "2026-10-20T03:10:00Z"
  },
  "conversation": {"id": 7, "title": "반려동물 용품 쇼핑몰"},
  "initial_message": {
    "id": 12,
    "role": "user",
    "content": "반려동물 보호자를 위한 쇼핑몰을 기획해줘.",
    "created_at": "2026-10-20T03:10:00Z"
  }
}
```

`initial_message`가 없으면 응답의 `conversation`과 `initial_message`는 `null`이다. 소유자는 요청에서 받지 않고 현재 세션으로 설정한다.

### 3. Project 상세·수정

`GET /api/v1/projects/{project_id}/` → `200 OK`와 Project 객체. Project 소유자가 아니거나 없으면 `404 PROJECT_NOT_FOUND`.

`PATCH /api/v1/projects/{project_id}/`는 `title`, `summary`, `status` 중 수정할 필드만 받는다. Project 소유권을 확인하고 기존 생성과 같은 길이·상태 검증을 적용한다. 성공 시 갱신한 Project 객체를 반환한다. 소유자가 아니거나 없으면 `404 PROJECT_NOT_FOUND`.

### 4. Conversation 생성

`GET /api/v1/projects/{project_id}/conversations/`는 Project 소유자의 대화 목록을 `updated_at DESC, id DESC` 순으로 반환한다.

```json
{"items":[{"id":7,"project_id":41,"title":"반려동물 쇼핑몰 기획","created_at":"2026-10-20T03:10:00Z","updated_at":"2026-10-20T03:10:00Z"}]}
```

`POST /api/v1/projects/{project_id}/conversations/`

```json
{"title": "반려동물 쇼핑몰 기획"}
```

`title`은 선택값이며 생략하면 Project 제목을 사용한다. Project 소유권을 검증하고 `201 Created`와 `{ "id", "project_id", "title", "created_at", "updated_at" }`를 반환한다.

### 5. Message 조회·저장

- `GET /api/v1/projects/{project_id}/conversations/{conversation_id}/messages/?limit=50&cursor={opaque}`
- `POST /api/v1/projects/{project_id}/conversations/{conversation_id}/messages/`

POST body:

```json
{"content": "주요 고객을 1인 가구로 잡아줘."}
```

서버가 `role: "user"`를 부여한다. `content`는 trim 후 1–10,000자다. 응답은 `201 Created`와 `{ "id", "conversation_id", "role", "content", "created_at" }`. 클라이언트는 role을 지정할 수 없다. 기존 프로젝트 화면의 임시 Supervisor 응답은 서버가 생성해 저장하고, 이후 Run 실행 응답은 같은 원칙으로 서버가 기록한다.

조회는 같은 Conversation의 메시지를 `created_at ASC, id ASC`로 페이지화한다. URL의 Project, Conversation, 세션 User 소유 관계가 모두 일치해야 한다.

### 6. Run 생성과 멱등성

`POST /api/v1/projects/{project_id}/runs/`

필수 헤더: `Idempotency-Key: <UUID>`

```json
{
  "conversation_id": 7,
  "source_message_id": 12,
  "previous_run_id": null,
  "feedback": null
}
```

- 서버는 Project·Conversation·Message의 소유자와 소속이 모두 같은지 확인한다. `source_message_id`는 해당 Conversation의 `user` 메시지여야 한다.
- `requested_by`, 상태, 실행 순서는 서버가 설정한다. 새 Run은 `queued`로 저장한 뒤 `202 Accepted`와 Run 자원, `Location: /api/v1/projects/{project_id}/runs/{run_id}`를 반환한다.
- 서버는 요청 내용을 instruction snapshot으로 구조화하고, 같은 트랜잭션에서 `queued` Planning Task 하나를 연결한다. MVP의 Supervisor 구조화는 규칙 기반이며 LLM 호출은 하지 않는다. Run 응답에는 연결된 Task의 `id`, `title`, `status`가 포함된다.
- Run POST는 worker를 동기 호출하지 않는다. 별도 `manage.py process_runs` worker가 queued Run을 가져가 Planning execution을 수행하고 `GET` 상태 조회에서 결과 상태를 확인한다. 기본 provider는 재현 가능한 fake이며, 외부 provider adapter는 아직 없다.
- 완료한 Planning PRD는 프로젝트·Task·AgentExecution에 연결된 DB Artifact로 버전 저장한다. `GET /api/v1/projects/{id}/artifacts/`는 소유자 결과 목록, `GET .../{artifact_id}/`는 상세 JSON, `GET .../{artifact_id}/download/`는 JSON 첨부 다운로드를 제공한다. 파일 경로나 저장소 내부 위치는 응답하지 않는다.
- Artifact의 `.../{artifact_id}/reflection/` POST는 활성 기준으로 평가를 저장하고, GET은 결과를 반환한다. 평가 시점의 기준 snapshot, 항목별 점수·근거·가중치, 개선안은 Artifact에 연결되어 보존된다. 현재 평가는 명시적으로 개발용 mock이며 실제 LLM 심사가 아니다.
- `GET /api/v1/projects/{id}/events/`는 소유자 프로젝트의 Run·Task·Execution 이벤트를 최신순 제공한다. 프로젝트 상세의 최근 활동도 동일 이벤트 레코드에서 읽는다.
- `POST /api/v1/projects/{id}/runs/{run_id}/retry/`는 재시도 가능한 실패만 새 queued Run으로 만든다. `Idempotency-Key` UUID가 필수이며 이전 Run과 instruction snapshot을 보존한다. 연속 재시도는 최대 3회이며 오류 payload에 code·사용자 메시지·retryable을 포함한다.
- `POST /api/v1/projects/{id}/runs/{run_id}/cancel/`은 queued 실행을 즉시 취소하고 running 실행은 `cancel_requested`로 표시한다. Worker는 Provider 응답 경계에서 취소 상태를 확인하고 결과 저장 없이 cancelled 처리한다. `POST .../{run_id}/regenerate/`는 새 사용자 메시지와 피드백으로 새 Run을 만들며 이전 결과·Artifact 버전을 유지한다.
- AgentExecution은 provider/model 이름, nullable token 수, nullable 추정 비용을 저장한다. 현재 provider는 토큰·비용을 계측하지 않아 관리 화면에 `미계측`으로 표시한다. 관리자 Tasks/Executions 페이지는 실제 Task·Execution DB와 상태 필터·검색을 사용한다.
- 동일 Project·같은 `Idempotency-Key`·같은 `source_message_id` 재요청은 새 Run을 만들지 않고 기존 Run을 `200 OK`로 반환한다. 첫 응답을 못 받은 클라이언트가 안전하게 재시도할 수 있다.
- 키가 같은데 `source_message_id`가 다르면 `409 IDEMPOTENCY_KEY_REUSED`를 반환한다. DB의 `(project_id, idempotency_key)` unique 제약이 동시 요청을 최종 방어한다.
- 이 POST는 Worker를 동기 실행하지 않는다. `queued`를 저장하고 별도 실행 경계에 넘긴다. 동시 실행 상한은 이 계약에서 임의로 추가하지 않으며 운영값 검토 때 결정한다.

```json
{
  "id": 73,
  "project_id": 41,
  "conversation_id": 7,
  "source_message_id": 12,
  "status": "queued",
  "progress": 0,
  "created_at": "2026-10-20T03:11:00Z",
  "started_at": null,
  "finished_at": null
}
```

Run 상태값: `queued`, `running`, `cancel_requested`, `cancelled`, `succeeded`, `failed`. 허용 상태 전이는 서버에서 검사한다. 취소 요청은 Day 16 별도 동작으로 추가한다.

### 7. Run 상태 조회

`GET /api/v1/projects/{project_id}/runs/{run_id}/` → `200 OK`와 Run 자원. Project 소유권을 매번 검사한다. 실패 시 오류 코드와 사용자 메시지를 반환하되 내부 경로, stack trace, Provider secret은 포함하지 않는다. 상태 갱신이 필요하면 클라이언트는 조회를 재호출하며, 푸시 연결은 MVP 범위에 없다.

### 8. Artifact 조회·다운로드

- `GET /api/v1/projects/{project_id}/artifacts/?logical_key={key}&limit=25&cursor={opaque}` — Project 산출물 목록, `200 OK`.
- `GET /api/v1/projects/{project_id}/artifacts/{artifact_id}/` — 메타데이터, `200 OK`.
- `GET /api/v1/projects/{project_id}/artifacts/{artifact_id}/download/` — 서버가 Project 소유권·파일 권한을 검사한 뒤 파일을 전송한다.

Artifact 응답은 `{ "id", "project_id", "task_id", "logical_key", "version", "title", "artifact_type", "created_at", "download_url" }`. 실제 `file_path`는 반환하지 않는다. 새 실행 결과는 같은 `logical_key`의 새 `version`으로 추가해 과거 성공 결과를 덮어쓰지 않는다.

## 공통 오류 형식

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "프로젝트 이름은 2자 이상 입력해 주세요.",
    "details": {"title": "min_length"},
    "request_id": "req_01J..."
  }
}
```

| HTTP | 코드 예 | 의미 |
| --- | --- | --- |
| 400 | `INVALID_JSON` | JSON 문법 오류 |
| 401 | `AUTH_REQUIRED` | 세션 로그인 필요 |
| 403 | `CSRF_FAILED` | CSRF token 누락·오류 |
| 404 | `PROJECT_NOT_FOUND`, `RUN_NOT_FOUND`, `ARTIFACT_NOT_FOUND` | 없거나 요청자 소유가 아님 |
| 409 | `IDEMPOTENCY_KEY_REUSED`, `RUN_STATE_CONFLICT` | 같은 요청 키의 본문 불일치 또는 현재 상태에서 불가 |
| 422 | `VALIDATION_ERROR` | 필드 형식·길이·상태값 오류 |
| 500 | `INTERNAL_ERROR` | 로그에는 request_id와 내부 원인을 남기고 응답은 안전한 문구만 반환 |

## Day 5 이후 구현 확인 항목

- Django JSON API 전용 인증 실패·CSRF 실패 응답을 HTML 페이지 응답과 분리한다.
- 프로젝트·Conversation·Message·Run 저장을 같은 소유권 서비스와 트랜잭션 경계로 연결한다.
- Conversation 목록·Message 조회/저장 시 Project·Conversation·User의 소유 관계를 모두 검증한다.
- 동시 동일 idempotency 요청에서 DB unique 충돌을 잡고 기존 Run을 다시 읽는다.
- 파일 다운로드 요청마다 DB 메타데이터와 실제 저장 경로를 서버에서 검증한다.
