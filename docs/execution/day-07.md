# Day 7 — Conversation / Message 저장

- 수행일: 2026-10-26
- 기준 문서: `기획/1. 기획안.txt` Day 7, Day 3 DBML, `docs/contracts/project-execution-api-v1.md`
- 상태: 완료 (Project별 Conversation·Message API와 상세 채팅 UI를 DB에 연결)

## 1. 수행 내용

- 기존 Project 상세 채팅 패널의 디자인, 가이드 탭, 열기·닫기·확장 버튼은 유지하면서 React가 대화 목록·메시지 전송 상태를 관리하도록 바꿨다.
- 상세 화면 진입 시 로그인 사용자가 소유한 프로젝트 대화 목록을 가져온다. 대화가 없으면 기본 대화를 만들고, 선택한 대화의 메시지를 읽어 채팅창에 복원한다.
- 새 대화 생성, 대화 전환, 사용자 메시지 전송을 구현했다. 입력 내용은 메시지 API에 저장한 뒤 기존 임시 Supervisor 응답을 서버에서 만들고 같은 대화에 저장한다. 새로고침 후 양쪽 메시지가 다시 나타난다.
- `GET/POST /api/v1/projects/{id}/conversations/`와 `GET/POST /api/v1/projects/{id}/conversations/{conversation_id}/messages/`를 추가했다. 메시지 조회는 `created_at ASC, id ASC` cursor 페이지네이션을 제공한다.
- 매 요청에서 Project owner, Conversation owner, URL의 Project–Conversation 관계를 확인한다. 클라이언트는 메시지 role을 설정할 수 없고, user 메시지만 보낼 수 있다.
- 메시지 저장 시 Conversation과 Project의 `updated_at`을 갱신한다. 기존 임시 chat POST도 owner 검사를 거치며 서버 응답을 저장한다.
- API 계약에서 완료된 범위와 임시 Supervisor 응답 저장 방식을 명확히 했다. Day 9 이후 실제 Planning/Run 결과가 이 임시 응답을 대체할 수 있도록 서버 생성 메시지 경계를 유지한다.

## 2. 검증 결과

| 검증 | 결과 |
| --- | --- |
| 전체 Django 테스트 | 31개 통과 |
| API 대화 생성·메시지 저장·재조회 | 새 Client로 반복 조회해 저장된 내용 확인 |
| Project / Conversation 소유권 및 URL 관계 | 타 사용자·다른 프로젝트 조합 404 확인 |
| 메시지 입력 검증 및 cursor 페이지 | 빈 메시지 거부, 오름차순 2개 단위 페이지 경계 확인 |
| 임시 Supervisor 응답 | assistant role 응답이 같은 Conversation에 저장됨 확인 |
| `manage.py check` | 통과 |
| `makemigrations --check --dry-run` | 추가 migration 없음 (Day 6에서 테이블 생성 완료) |
| React production build | Vite 6.4.1, 1,647 modules 빌드 통과 |
| Git whitespace 검사 | `git diff --check` 통과 |

## 3. 발견·보완 사항

- 이전 전송 경로는 입력을 화면에만 추가하고 DB에 남기지 않아 새로고침하면 사라졌다. User Message 저장 후 서버 응답도 저장하고, 진입 시 API에서 다시 읽도록 연결했다.
- 채팅 패널은 React DOM과 구형 스크립트가 전송 이벤트를 나눠 관리했다. 채팅창 form 전송과 열기·닫기·확장 상태를 React로 옮겨 한 번의 전송이 중복 저장되지 않도록 했다. `chat.js`의 가이드 탭 비간섭 동작은 유지했다.
- 새 대화·메시지 조회에서 Project ID와 Conversation ID가 서로 어긋나는 요청을 owner 조건과 함께 거부한다.

## 4. 변경 파일

- API 경로·권한·응답: `front/apps/projects/api_urls.py`, `api_views.py`, `ownership.py`
- 저장 서비스와 기존 임시 채팅 응답: `front/apps/projects/services.py`, `views.py`
- React 채팅 UI: `front/react/src/pages/AllPages.tsx`
- 회귀 검증: `front/apps/projects/tests.py`, `front/apps/accounts/tests.py`
- 계약: `docs/contracts/project-execution-api-v1.md`

## 5. 남은 검증 범위

- 전체 Django 테스트와 production build로 서버·번들 동작은 확인했다. 실제 브라우저 viewport screenshot과 수동 클릭 시각 검수는 별도로 수행하지 않았다.
- 임시 Supervisor 답변은 기존 결정형 stub이며 LLM 또는 Agent 실행 결과가 아니다. 실제 Planning 실행 연결은 Day 8–10 흐름에서 다룬다.
- 메시지 API는 최대 100개 cursor 페이지를 지원한다. 현재 채팅 화면은 첫 페이지를 자동으로 읽으며, 오래된 대화의 추가 페이지 로딩 버튼은 아직 없다.
