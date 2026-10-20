# Day 4 — Project 실행 API 계약

- 수행일: 2026-10-20
- 기준 문서: `기획/1. 기획안.txt` 15-2, 16장; Day 3 DBML
- 상태: 완료 (계약 초안, API 구현은 후속 일자)

## 1. 기존 요청 흐름 점검

- React 화면은 Django가 만든 `sb-react-data` JSON payload를 받아 그린다. `front/react/src/api.ts`에는 React Query client와 초기 payload parser가 있으나 실제 Project/Run API 호출은 없다.
- Project 생성은 현재 HTML form POST `/projects/create/`로 `mockdata.create_project`를 호출한다.
- 프로젝트 Chat은 기존 `/projects/{id}/chat/`에서 Stub JSON을 반환한다. Message나 Conversation 저장은 없다.
- 따라서 기존 Stub URL을 그대로 영구 API로 확장하지 않고, 화면 URL과 공존할 `/api/v1` 계약을 정리했다.

## 2. 확정한 요청 흐름

1. Project 생성 요청에 선택 `initial_message`가 있으면 Project·기본 Conversation·user Message를 한 번에 저장한다.
2. 이후 대화는 Message 생성 API로 먼저 저장한다.
3. 실행 요청은 저장된 Message ID를 참조하고 `Idempotency-Key`로 Run 중복 생성을 막는다.
4. Run API는 `queued` 응답을 바로 돌려주고 Worker 실행은 HTTP 요청 밖에서 처리한다.
5. 화면은 Run 상태를 조회하고 Project 소유권 확인이 된 Artifact metadata/download API로 결과를 읽는다.

이 흐름은 Day 3의 필수 `source_message_id`, `conversation_id`, `(project_id, idempotency_key)`와 일치한다. Run 중복 요청에서 같은 키·같은 메시지는 기존 Run을 반환하고, 같은 키·다른 메시지는 충돌로 처리한다.

## 3. 오류·권한 기준

- API 인증 실패는 페이지 redirect가 아니라 JSON 401이다. CSRF 실패는 JSON 403이다.
- 다른 사람의 Project·Conversation·Message·Run·Artifact는 존재 여부를 노출하지 않도록 404로 통일한다.
- 클라이언트가 owner ID·role을 전달하지 못하게 하고, Run 생성 전 Project와 source Message 소속을 서버에서 함께 검증한다.
- 잘못된 JSON(400), 유효성 오류(422), 키 재사용 불일치(409), 안전한 내부 오류(500)를 공통 JSON envelope로 정의했다.
- 외부 LLM 호출, task 취소, 실시간 푸시, 임의 동시성 제한은 이번 API 계약에서 구현하거나 가정하지 않는다.

## 4. 산출물 및 검수

- 상세 요청·응답·상태·멱등성·오류 계약: `docs/contracts/project-execution-api-v1.md`
- 예시 JSON의 자원 ID는 설명용 값이며 실제 DB와 연결된 결과가 아니다.
- Django system check와 전체 `apps` 테스트를 다시 실행해 계약 작업 전 기준선 회귀가 없는지 확인한다.
- 화면 URL, Session/CSRF 구조, DBML 설계는 검토했으며 브라우저 시각 검수는 Day 1 미완료 상태로 남아 있다.

## 5. Day 5 선행 조건

다음 구현은 Django 모델·마이그레이션과 실제 User identity mapping을 전제로 한다. API view를 먼저 추가하지 않고, 모델 및 소유권 서비스가 준비된 뒤 `transaction.atomic()` 안에서 Project/Conversation/Message를 저장하고, API 전용 JSON 인증·오류 처리를 연결한다.
