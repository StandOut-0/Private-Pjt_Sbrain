# Day 6 — Project 저장 흐름

- 수행일: 2026-10-20
- 기준 문서: `기획/1. 기획안.txt` Day 6, Day 3 DBML, `docs/contracts/project-execution-api-v1.md`
- 상태: 완료 (Project 목록·생성·조회·수정의 DB 경로, 소유자별 화면 연결)

## 1. 수행 내용

- 대시보드, 프로젝트 목록, 사이드바의 Project payload를 현재 로그인 계정 소유 DB 행으로 통일했다. 다른 계정의 프로젝트와 공용 샘플 프로젝트가 사용자 화면에 섞이지 않는다.
- 프로젝트 목록의 검색·상태 필터를 DB 쿼리로 전환했다. 기존 React 필터 값 `running/done/ready`와 모델 값 `active/completed/archived`를 서버에서 변환해 화면 UI를 유지한다.
- 새 프로젝트 팝업의 POST를 DB 생성 서비스로 연결했다. 이름 2–80자, 설명 최대 500자, 목표 최대 10,000자를 서버에서 검증하고 계정 owner는 세션에서만 결정한다.
- 팝업의 목표 문구는 입력 손실을 막기 위해 Project·Conversation·User Message를 하나의 트랜잭션으로 저장한다. 따라서 Conversation/Message의 최소 테이블과 migration을 Day 6에 앞당겨 추가했다. Day 7에는 대화 조회·추가·새로고침 복구 경로를 별도로 구현한다.
- API `GET/POST /api/v1/projects/`와 `GET/PATCH /api/v1/projects/{id}/`를 연결했다. 목록은 소유자 조건, 필터, cursor pagination을 적용하고 변경은 owner 검증 후 수행한다.
- DB에 없는 임의 ID를 상세 URL에 넣어도 Mock 프로젝트로 보이지 않게 했다. 기존 계정 스모크 테스트는 고정 ID 대신 실제 owner Project를 만든다.
- API 계약서에서 Project 구현 완료 범위를 표시하고 목록·상세·수정 URL과 계약을 맞췄다.

## 2. 검증 및 분석

| 검증 | 결과 |
| --- | --- |
| 전체 Django 테스트 | 27개 통과 |
| `manage.py check` | 통과 |
| `makemigrations --check --dry-run` | 추가 migration 없음 |
| 개발 SQLite | `projects.0002_conversation_message_and_more` 적용 완료 |
| React `npm run build` | Vite 6.4.1, 1,647 modules 빌드 통과 |
| 프로젝트 검색·상태 필터 | owner scope 포함 테스트 통과 |
| 팝업 POST·초기 목표 저장 | Project/Conversation/Message owner 및 본문 테스트 통과 |
| API 생성·수정·소유권·cursor | 성공, 검증 오류, 타 사용자 접근, 중복 없는 페이지 경계 테스트 통과 |
| 대시보드·사이드바 | 소유자 프로젝트만 포함되는 payload 테스트 통과 |
| Git whitespace 검사 | `git diff --check` 통과 |

## 3. 발견한 기존 문제와 수정

- Project 목록이 전역 Mock 목록을 사용해 계정별 데이터 경계가 없었다. 대시보드와 navigation까지 같은 owner query로 전환했다.
- 공용 샘플 Mock 상세 fallback 때문에 DB에 없는 URL이 예시 프로젝트처럼 보일 수 있었다. 사용자 상세는 실제 소유 DB 행만 렌더링한다.
- Day 4 계약의 초기 목표 저장을 생성 화면이 무시하고 있었다. 프로젝트 생성 트랜잭션에서 최초 사용자 메시지로 보존한다.
- 테스트 중 dashboard notifications의 기존 Mock import가 누락되면 페이지가 깨지는 경로를 발견해 유지했다.

## 4. 변경 파일

- 모델·migration: `front/apps/projects/models.py`, `front/apps/projects/migrations/0002_conversation_message_and_more.py`
- Project 저장/권한/API: `front/apps/projects/services.py`, `ownership.py`, `views.py`, `api_views.py`, `api_urls.py`
- 사용자 화면 payload: `front/apps/dashboard/views.py`, `front/apps/react_pages.py`
- 생성 팝업 입력 제한: `front/react/src/components/AppShell.tsx`
- 검증: `front/apps/projects/tests.py`, `front/apps/accounts/tests.py`
- API 계약: `docs/contracts/project-execution-api-v1.md`

## 5. 시각 점검과 남은 작업

- React production build와 서버 렌더링 payload 테스트로 화면 연결을 확인했다. Computer Use 브라우저 런타임의 경로 오류가 지속돼 실제 브라우저 screenshot과 viewport별 육안 확인은 완료하지 못했다.
- Project 수정은 API로 제공한다. 화면 내 이름/설명 편집 UI는 현재 페이지 설계에 없어 추가하지 않았다.
- Day 7에는 대화 목록/메시지 조회·추가 API와 기존 프로젝트 채팅 UI를 저장 상태에 연결하고 새로고침 복구를 검증한다.
- 사용자 작성 `기획/4. 회의 - 아이디어 반영.txt` 변경은 이번 작업에 포함하지 않았다.
