# Day 10 — Planning Agent 최소 실행

- 수행일: 2026-10-26
- 기준 문서: `기획/1. 기획안.txt` Day 10, Day 9 instruction snapshot, API 계약
- 상태: 완료 (fake Planning provider, PRD JSON, 실패 저장, DB worker 명령)

## 1. 수행 내용

- `apps.execution.Agent`와 `AgentExecution`을 추가해 Task별 Planning 실행, 시도 번호, 입출력, 상태, 오류 코드·메시지·재시도 가능 여부와 시각을 저장한다.
- Planning provider 계약은 `generate(instruction_snapshot) -> PRD object`이며 필수 키·자료형·크기를 검사한다. provider 결과가 계약을 위반하면 `INVALID_PROVIDER_OUTPUT`으로 종료한다.
- `FakePlanningProvider`는 같은 snapshot 입력에 같은 PRD JSON을 돌려준다. 목표·명시 요구사항·사용 흐름·완료 기준·미정 질문을 분리하며, 제공되지 않은 사용자/도메인 정보를 사실처럼 채우지 않는다.
- `PLANNING_PROVIDER=fake`가 기본값이다. external 선택은 DEBUG 개발환경에서도 adapter 미설정 오류로 명확히 실패하며, DEBUG 외부환경에서는 `PROVIDER_NOT_ALLOWED`로 차단한다. 외부 네트워크나 비밀키는 사용하지 않는다.
- API 요청을 동기 실행하지 않도록 DB polling management command `manage.py process_runs`를 추가했다. `--once`, `--run-id`, `--poll-seconds` 옵션을 제공한다. worker가 Run·Task·Execution을 running으로 바꾸고 결과에 따라 모두 성공/실패로 종료한다.
- 실패 시 사용자에게 보여줄 안전 메시지와 내부 구조화 오류 코드를 분리한다. 예외 stack trace와 원문 Provider 출력은 API 응답에 노출하지 않고 서버 로그에는 예기치 않은 실패의 실행 ID만 문맥으로 남긴다.

## 2. 검증 결과

| 검증 | 결과 |
| --- | --- |
| 전체 Django 테스트 | 39개 통과 |
| Fake PRD 재현성 | 동일 요청 2회 결과 일치 |
| 성공 실행 | Run·Task·AgentExecution 모두 succeeded, PRD JSON 저장 |
| Provider timeout | failed, `PROVIDER_TIMEOUT`, 재시도 가능 표시 및 안전 메시지 저장 |
| 잘못된 provider 출력 | `INVALID_PROVIDER_OUTPUT`으로 구조화 실패 |
| 외부 provider 환경 경계 | DEBUG=False에서 외부 provider 거부 |
| worker 빈 큐 `--once` | 정상 종료 및 안내 문구 확인 |
| Django check / migration drift | 통과 / 추가 migration 없음 |
| 실행 DB migration | `execution.0003_agent_agentexecution`, `0004_agentexecution_is_retryable` 적용 |
| `git diff --check` | 통과 |

## 3. 분석 및 한계

- PRD는 실제 LLM 응답이 아니라 명시적으로 `provider: fake`인 구조화 예시다. UI/API에서 이를 외부 AI가 만든 확정 결과라고 표시하지 않는다.
- 별도 worker 프로세스를 실행해야 Run이 queued에서 바뀐다. 기본 runserver만 실행한 상태에서는 Run이 대기열에 남는 것이 계약상 정상이다.
- AgentExecution 결과는 DB에 저장했지만 Artifact 버전 및 다운로드 권한으로는 아직 노출하지 않는다. Day 11에서 실행 결과를 Artifact로 발행한다.
- 프론트는 이번 Day에 바꾸지 않았다. fake provider, 상태 전이, migration과 전체 Django API를 검증했다.

## 4. 변경 파일

- 실행 모델·migration: `front/apps/execution/models.py`, `migrations/0003_agent_agentexecution.py`, `0004_agentexecution_is_retryable.py`
- Planning 계약·worker: `front/apps/execution/planning.py`, `management/commands/process_runs.py`
- 회귀 테스트와 API 계약: `front/apps/execution/tests.py`, `docs/contracts/project-execution-api-v1.md`
