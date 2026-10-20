# Day 5 — DB·계정 식별·Project 소유권 기반

- 수행일: 2026-10-20
- 기준 문서: `기획/1. 기획안.txt` 15-2, 16장; Day 3 DBML; Day 4 API 계약
- 상태: 완료 (UserAccount·Project 기반 적용, 전체 Project 화면 연결은 Day 6)

## 1. 적용한 저장 구조

- Django `UserAccount`를 추가해 session login identity를 영속 사용자 레코드로 연결했다. `identity_key`가 고유 식별자이고 이메일은 표시·연락 값이다.
- 일반 사용자·관리자는 현재 서버의 임시 로그인 흐름에서 정해진 이메일 identity로 연결한다. 실제 OAuth subject는 아직 없다.
- 체험 로그인은 이메일·provider 토큰을 저장하지 않고 세션마다 서버가 임의 guest identity를 만든다. DB `role`은 `user`로 두며 `demo` 역할은 세션에만 남긴다. 체험 세션마다 다른 소유자 레코드가 생성된다.
- `Project.owner`는 `PROTECT` FK로 계정을 참조하고 DB column은 DBML의 `user_id`를 사용한다. 물리 테이블은 예약어 충돌을 피하기 위해 Django에서 `sb_user`, `sb_project`로 명명했다. 키 column은 `user_id`, `project_id`로 맞췄다.
- 계정/Project `0001_initial` 마이그레이션을 추가하고 기존 SQLite 데이터는 지우지 않은 채 두 테이블만 추가했다.

## 2. 권한 연결

- 로그인 시 세션 키를 교체하고 DB UserAccount를 생성/조회한 뒤 내부 `user_id`를 세션에 저장한다. 로그아웃은 세션을 flush한다.
- 일반 `login_required`는 유효한 UserAccount가 있는 세션만 허용한다. 관리자 기능은 세션의 `is_admin` 표시값 대신 DB 계정의 `role`을 확인한다.
- 실제 DB Project 상세 페이지와 `GET /api/v1/projects/{project_id}/`는 매번 소유 계정을 확인한다. 소유자가 아니거나 없는 Project는 같은 404로 응답한다.
- API 비로그인 응답은 HTML redirect가 아니라 계약에 맞는 JSON 401을 반환한다.
- 현재 정적 `mockdata` Project는 공용 예시 데이터다. DB에 저장된 Project ID가 있으면 DB 행을 우선 조회해 비소유자 접근을 숨긴다. Mock 목록·생성은 Day 6에서 DB로 전환한다.

## 3. 변경 파일

- 모델: `front/apps/accounts/models.py`, `front/apps/projects/models.py`
- 계정 연결: `front/apps/accounts/session.py`
- 소유권·조회: `front/apps/projects/ownership.py`, `front/apps/projects/api_views.py`, `front/apps/projects/api_urls.py`, `front/apps/projects/views.py`
- URL: `front/config/urls.py`
- 마이그레이션: `front/apps/accounts/migrations/0001_initial.py`, `front/apps/projects/migrations/0001_initial.py`
- 회귀 검증: accounts / projects 테스트

## 4. 검증 결과

| 검증 | 결과 |
| --- | --- |
| Django system check | 통과 |
| `makemigrations --check --dry-run` | 추가 생성할 migration 없음 |
| 개발 SQLite migration | `accounts.0001_initial`, `projects.0001_initial` 적용 완료 |
| Django 앱 테스트 | 20개 통과 |
| 소유자 상세 페이지/API | 모두 200, API 응답에서 Project 필드 확인 |
| 타 사용자 상세 페이지/API | 모두 404, API `PROJECT_NOT_FOUND` 확인 |
| 비로그인 Project API | JSON `401 AUTH_REQUIRED` 확인 |
| 세션 role만 관리자라고 표시 | DB role이 user면 관리자 페이지 접근 거부 확인 |
| 체험 로그인 | 세션별 다른 UserAccount identity 생성 확인 |
| 로컬 서버 `/login/` | HTTP 200 |

## 5. 현재 남은 범위

- Project 목록과 생성 폼은 아직 Mock을 사용한다. Day 6에서 DB 저장·소유자별 목록·상세 payload를 연결한다.
- `/api/v1/projects/{id}` 조회만 먼저 구현했다. 생성·Conversation·Message·Run·Artifact API는 계약 순서에 따라 후속 구현한다.
- 현재 일반/관리자 로그인은 개발용 고정 계정이다. 다중 실제 계정과 OAuth subject 연동은 범위 밖이다.
- 체험 세션 종료 후 guest Project 데이터를 보존/삭제하는 정리 작업은 Day 18 보존 정책에서 다룬다.
- 브라우저 screenshot 기반 시각 검수는 Computer Use 런타임 경로 오류로 아직 못 했다. Django 응답·React mount 테스트만 통과했다.

## 6. Day 6 선행 조건

Project 목록을 DB owner 기준으로 조회하고, 생성 POST도 현재 계정 owner를 서버에서 설정한다. 유효성 오류·빈 목록·필터·타 사용자 ID 변조를 테스트한다. 초기 `goal`은 DB Conversation/Message 모델이 준비되는 Day 7에 저장 경로를 연결한다.
