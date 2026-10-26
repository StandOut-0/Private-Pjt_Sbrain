# Day 14 실행 보고서 — 공통 실행 이벤트

## 구현

- Run, Task, AgentExecution을 선택적으로 연결하는 공통 `ExecutionEvent`를 추가했다.
- Planning worker가 Agent 시작·성공/실패 및 Run 성공/실패 이벤트를 기록한다. Run 생성 경로는 queued 이벤트도 남긴다.
- `GET /api/v1/projects/{id}/events/`는 로그인한 프로젝트 소유자에게 최근 이벤트를 제공한다.
- 프로젝트 상세의 기존 `activities` payload가 공통 이벤트 테이블을 읽도록 연결해 Timeline과 Activity Log의 원천 데이터를 통일했다.

## 검증

- Event migration 적용 완료.
- `manage.py test apps.execution apps.projects apps.reflection`: 27개 통과. 성공 흐름의 이벤트 순서, 프로젝트 활동 payload 및 기존 소유권/API 흐름을 확인했다.
- 관련 시스템 점검은 테스트 시작 시 이상 없음으로 통과.

## 제한 사항

- 실행은 현재 동기 fake provider 기반이므로 이벤트는 단계 사이에 발생하며, 실시간 push/WebSocket은 연결하지 않았다.
- 기존 상세 화면은 페이지 진입 시 초기 payload를 받는다. 자동 새로고침/폴링은 후속 작업 대상이다.
