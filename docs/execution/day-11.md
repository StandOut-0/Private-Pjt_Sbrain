# Day 11 실행 보고서 — Artifact 버전과 접근 경계

## 구현

- Planning 성공 결과를 DB `Artifact`로 저장하고 Project, Task, AgentExecution과 연결했다.
- `logical_key`와 project별 증가 버전을 저장해 재생성 결과를 보존한다.
- 프로젝트 소유자 범위의 Artifact 목록·상세·JSON 다운로드 API를 추가했다. 타인 프로젝트는 404, 비로그인 요청은 401이다.
- DB에 내용을 저장하므로 서버 파일 경로를 노출하거나 임의 경로 다운로드하지 않는다.

## 검증

- `manage.py migrate --noinput`: Artifact migration 적용 완료.
- `manage.py test apps.execution`: 7개 통과. 성공한 PRD의 Artifact 저장, 상세/목록/다운로드, 타인 소유 프로젝트 차단 확인.
- `manage.py check`: 이상 없음.
- `manage.py makemigrations --check --dry-run`: 변경 없음.
- `git diff --check`: 공백 오류 없음.

## 제한 사항

- 저장소는 DB JSON 한 종류이며 업로드 파일, 보존 기간, 대용량 산출물 정책은 Day 18에서 점검한다.
- 같은 logical key의 버전 번호는 현재 동기 worker 기준 count로 생성한다. 다중 worker의 동시 생성은 유니크 제약이 방어하며 운영 DB에서 재시도 전략을 추가 점검해야 한다.

## 다음 작업

Day 12에서 평가 기준과 가중치 합계 검증, 평가 시점의 기준 snapshot을 추가한다.
