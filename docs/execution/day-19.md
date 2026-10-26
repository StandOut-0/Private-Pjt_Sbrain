# Day 19 실행 보고서 — 종단 간 인수 시나리오

## 검증한 시나리오

1. 세션 로그인 상태에서 프로젝트·초기 Conversation·사용자 Message 생성.
2. idempotency key로 Run 제출 후 queued 응답을 받고 Worker가 Planning을 완료.
3. Run 상태 조회, Artifact 목록 및 소유자 제한 다운로드.
4. Artifact 버전에 Reflection 평가 생성, 기준 snapshot/근거 저장.
5. 공통 실행 Event 조회와 프로젝트 상세 React payload의 Artifact/Reflection 연결 확인.
6. 다른 사용자가 프로젝트 Artifact 목록·다운로드에 접근하면 404로 차단.

## 보완

- 프로젝트 상세 결과 영역을 mock tree에서 실제 Artifact 목록/JSON 다운로드로 연결했다.
- 실제 Reflection이 있을 때 점수·근거·보완 제안을 표시하고, 아직 없으면 해당 Artifact에서 평가를 시작할 수 있게 했다. mock 평가 배지를 함께 표시한다.
- 결과가 없을 때 빈 상태를 안내한다.

## 검증 결과

- `manage.py test`: 전체 53개 통과. 종단 간 생성→실행→Artifact→Reflection→화면 payload 및 소유권 차단을 확인했다.
- `npm run build`: React production build 성공.
- `manage.py check`, migration drift 확인 및 `git diff --check`: 통과.

## 미해결 결함/제한

- 실제 LLM/provider는 연결되지 않았고 Planning/Reflection은 개발 fake/mock이다.
- worker는 별도 관리 명령으로 실행해야 하며 서비스 관리자/작업 큐 복구 기능이 없다.
- 기본 DB는 SQLite이고 production backup·restore·retention 자동화가 없다. Day 18 운영 점검표를 production gate로 둔다.
- 브라우저 수동 시각 검수는 수행하지 않았으며 React build와 Django 응답 payload를 검증했다.
