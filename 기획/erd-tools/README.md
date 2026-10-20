# ERD 생성

원본: `../2. 초기 DB 설계, DBML(dbdiagram.io).txt`의 실제 `Table USER {`부터 끝까지.
산출물: `../erd.svg` (UTF-8, 확대 가능한 벡터), `validation.json` (원본 해시·관계 목록).

저장소 루트에서:

```powershell
npm ci --prefix 기획/erd-tools
node 기획/erd-tools/generate.cjs
python -B 기획/erd-tools/verify.py
```

DBML 공식 파서의 `dbml`·`dbmlv2`로 구문을 검사하고, 원본 필드·FK 개수와 참조 대상·타입을 대조한다.
별도 Python 검증은 SVG에 실제 표시된 모든 필드·타입·기본값·키·필수 여부·인덱스를 원본과 비교하고, 선의 시작·끝 좌표가 해당 필드 행에 도달하는지와 테이블 겹침 여부도 확인한다.
PK는 필수, `not null`이 없는 일반 필드는 nullable로 표시한다. 복합 고유 인덱스는 테이블 하단에 표시한다.
화살표는 FK 필드에서 참조 PK 필드로 향한다. 선에 마우스를 올리면 정확한 연결을 볼 수 있다.
타입·기본값·고유 키를 원본 그대로 표시하며, 상세 note는 SVG metadata에 보존한다.

생성 스크립트는 DBML을 변경하지 않는다. 이 ERD는 설계도이며 실제 DB 마이그레이션 상태를 뜻하지 않는다.
`2. 초기 erd.jpg`는 과거 설계 이미지이므로 최신 기준은 `erd.svg`이다.
미리보기 PNG와 DOT 중간 파일은 저장소 루트 `tmp/`에 생성하며 커밋하지 않는다.
