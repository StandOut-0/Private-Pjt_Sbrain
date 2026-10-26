# Day 13 실행 보고서 — Artifact Reflection

## 구현

- Artifact별 Reflection 평가 생성/조회를 연결했다. 완료된 Run과 Artifact 버전 및 기준 snapshot이 함께 저장된다.
- 항목별 점수, 적용 가중치, 근거, 개선 제안을 반환한다. 열린 질문·대상 사용자 미정의 시 후속 개선 문장을 제공한다.
- 같은 Artifact에 POST를 반복해도 기존 평가를 반환한다.
- 응답과 저장 행 모두 `is_mock=true` 및 `개발용 mock 평가`로 표시한다.

## 검증

- `manage.py migrate --noinput`: ReflectionReport migration 적용 완료.
- `manage.py test apps.reflection`: 4개 통과(기준 CRUD 권한·합계 검증, 평가 저장·snapshot·중복 호출·조회).
- `manage.py check`: 이상 없음.
- `manage.py makemigrations --check --dry-run`: 변경 없음.

## 제한 사항

- 현재 점수는 재현 가능한 규칙 기반 개발용 mock이다. 서비스 품질 측정이나 모델 성능 주장으로 사용하면 안 된다.
- 외부 LLM 기반 평가, 사용자가 감점 근거에 응답하는 흐름, 제품 UI는 이후 구현 대상이다.
