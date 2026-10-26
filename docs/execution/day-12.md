# Day 12 실행 보고서 — Reflection 평가 기준

## 구현

- 요구사항 충족 40, 흐름 완성도 25, 완료 기준 25, 가정·질문 명시 10의 초기 평가 기준을 데이터 migration으로 등록했다.
- 로그인 사용자는 기준 목록을 조회할 수 있다. 관리자만 기준 전체 교체를 할 수 있고, 활성 기준의 가중치 합이 100이 아니면 저장을 거절한다.
- 기준 정의를 Django Admin에서 조회할 수 있게 등록했다. aggregate 규칙을 우회하는 직접 편집은 제공하지 않는다.

## 검증

- migration 적용 완료.
- `manage.py test apps.reflection`: 3개 통과(초기 합계, 관리자 권한, 합계 오류의 저장 차단).
- `manage.py check`: 이상 없음.
- `manage.py makemigrations --check --dry-run`: 변경 없음.

## 제한 사항

- 관리자 기준 변경 화면은 JSON API이며 제품 화면 편집 UI는 아직 없다.
- 기준 변경은 과거 기록에 영향을 주지 않도록 다음 Day에서 snapshot으로 고정한다.
