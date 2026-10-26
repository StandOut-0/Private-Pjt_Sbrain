# Day 16 실행 보고서 — 중단과 재생성

## 구현

- queued Run은 즉시 취소하고 연결된 Task도 취소한다. running Run은 `cancel_requested`로 바꾸고 Provider 응답 경계에서 Worker가 취소·결과 폐기를 처리한다.
- 재생성 API는 완료/실패/취소된 이전 실행을 참조해 새 사용자 요청 메시지·개선 피드백으로 신규 Run을 만든다.
- 기존 Run, Artifact, Reflection 이력은 갱신/삭제하지 않고 새 PRD는 다음 버전으로 저장한다.
- 프로젝트 상세의 중단·재생성 확인 버튼을 API에 연결하고, 결과 보존 동작을 안내한다.

## 검증

- `manage.py test`: 전체 49개 통과. 대기 실행 취소, 실행 중 취소 요청의 결과 폐기, 재생성 후 이전 Artifact 보존 및 버전 증가를 확인했다.
- `manage.py check`: 이상 없음.
- `manage.py makemigrations --check --dry-run`: 변경 없음.
- `npm run build`: React production build 성공.
- `git diff --check`: 공백 오류 없음.

## 제한 사항

- 실행 중 취소는 Provider 응답이 반환된 후 처리되므로 외부 호출 자체를 강제 종료하지 않는다. Provider adapter별 timeout/cancel 지원이 필요하다.
- 프로젝트 상세의 화면은 페이지 초기 payload 방식이라 중단·재생성 후 reload하여 상태를 갱신한다.
