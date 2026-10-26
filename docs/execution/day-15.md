# Day 15 실행 보고서 — 실패 지점 재시도

## 구현

- 재시도 가능한 실패에 대해 새 Run과 Task를 만들고 원본 Run을 `previous_run`으로 연결한다. 원래 요청 snapshot·사용자 메시지·실패 실행은 유지된다.
- `POST /api/v1/projects/{id}/runs/{run_id}/retry/`에 UUID `Idempotency-Key`를 요구하고, 재시도 가능한 오류만 통과시킨다.
- 재시도 횟수를 Run에 저장하고 최대 3회로 제한했다. Run 조회 payload에 오류 코드·안전한 안내 문구·재시도 가능 여부를 포함한다.
- provider timeout은 실행 계층에서 `PROVIDER_TIMEOUT` 및 retryable 실패로 저장된다.

## 검증

- retry_count migration 적용 완료.
- `manage.py test apps.execution`: 9개 통과. 일시 실패 후 새 Run 성공, 원본 실패 기록 보존, 최대 3회 제한을 확인했다.
- Day 14 포함 worker·API 회귀 테스트도 통과.

## 제한 사항

- 외부 Provider adapter가 아직 없어 실제 네트워크 요청의 hard timeout은 구현 대상이 아니다. 향후 adapter는 반드시 connect/read timeout을 자체 설정해야 한다.
- 현재 실패 지점이 Planning 한 단계뿐이라 해당 Agent를 처음부터 재호출한다. 멀티 단계 부분 재개는 Agent 파이프라인 확장 이후 필요하다.
