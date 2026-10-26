# Day 17 실행 보고서 — 관리자 실행 관측과 비용 필드

## 구현

- AgentExecution에 provider/model, nullable input/output token 수, nullable USD 추정 비용 필드를 추가했다. 미측정 값을 0으로 가장하지 않는다.
- 관리자 Tasks/Executions 페이지를 mock 목록 대신 Task·AgentExecution·Project DB 조회로 전환했다. 제목·프로젝트·상태 검색과 성공률·실패율·평균 실행시간을 DB에서 계산한다.
- React의 token 열은 수치가 없는 경우 `미계측`을 표시한다.
- Django Admin에서 Run, Task, Agent, Execution, Event를 상태·Agent·Provider별로 검색/필터하고 비용·오류 필드를 확인할 수 있다.
- 재시도 호출 상한은 기존 최대 3회로 유지한다. 외부 provider 호출 상한은 현재 provider adapter가 없어 적용 대상이 없다.

## 검증

- AgentExecution usage migration 적용 완료.
- `manage.py test`: 전체 51개 통과. 관리자 DB 화면이 실제 project/task/provider를 표시하고 필터가 동작하는지 확인했다.
- `manage.py check`: 이상 없음.
- `manage.py makemigrations --check --dry-run`: 변경 없음.
- `npm run build`: React production build 성공.
- `git diff --check`: 공백 오류 없음.

## 제한 사항

- Fake provider는 token과 실제 비용을 만들지 않으므로 해당 값은 null이다.
- 관리자 Tasks 페이지의 trend는 생성 시각 기준 task 수이며 외부 모델 호출량·금액 시계열을 뜻하지 않는다.
