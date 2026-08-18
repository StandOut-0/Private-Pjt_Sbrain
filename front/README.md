# Second Brain

또 다른 나를 만드는 개인 AI 업무 파트너 Agent 플랫폼.

현재 단계는 **Frontend (Django Template + Bootstrap)** 구현이며,
Backend API / MySQL / Agent 연동은 이후 단계에서 진행한다.

---

## 0. 준비물 (Python이 없다면)

Python **3.10 ~ 3.13** 이 필요하다. 설치 여부 확인:

```powershell
python --version
```

`Python 3.x.x`가 안 나오면 설치한다.

- Windows: <https://www.python.org/downloads/windows/> 에서 설치.
  설치 화면에서 **Add python.exe to PATH** 체크 필수.
  (또는 PowerShell에서 `winget install -e --id Python.Python.3.12`)
- macOS: `brew install python@3.12`
- Ubuntu: `sudo apt install python3 python3-venv python3-pip`

설치 후 **터미널(PowerShell)을 새로 열어야** `python` 명령이 인식된다.

> Windows에서 `python`을 치면 Microsoft Store가 열리는 경우:
> 설정 → 앱 → 앱 실행 별칭 → `python.exe` / `python3.exe` 를 끈다.

---

## 1. 가장 쉬운 실행 (원클릭)

- Windows: 탐색기에서 `run.bat` 더블 클릭 (또는 PowerShell에서 `.\run.bat`)
- macOS / Linux: `bash run.sh`

가상환경 생성 → 패키지 설치 → DB 준비 → 서버 실행까지 자동으로 진행된다.
아래 수동 명령이 필요하면 2번 항목을 따른다.

---

## 2. 수동 실행 (Windows PowerShell)

```powershell
cd "C:\Users\Dell XPS 13\Desktop\sh\front\front\second-brain"

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

브라우저에서 <http://127.0.0.1:8000/login/> 접속.
종료는 터미널에서 `Ctrl + C`.

> `Activate.ps1` 실행이 차단되면(실행 정책 오류) 아래를 한 번 실행한 뒤 다시 시도한다.
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```
> cmd.exe를 쓴다면 활성화 명령은 `.\.venv\Scripts\activate.bat` 이다.

## 2-1. 수동 실행 (macOS / Linux)

```bash
cd second-brain
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

---

## 3. 로그인 방법 (임시 세션 로그인 / Backend 연동 전)

| 구분 | 방법 |
| --- | --- |
| 일반 사용자 | `Google로 로그인` 버튼 (실제 OAuth 아님) |
| 관리자 | `관리자로 로그인` → Face 인증 화면 → `얼굴 인증` 버튼 |
| 체험 | `체험 로그인` → 인증 코드 `SECONDBRAIN` |

관리자로 로그인해야 Tasks / Agents / Results / Coming Soon 관리 메뉴가 보인다.

---

## 4. 자주 나는 오류

| 증상 | 해결 |
| --- | --- |
| `'python'은(는) 내부 또는 외부 명령...` | Python 미설치 또는 PATH 미등록. 0번 항목 참고 후 터미널 재시작 |
| `ModuleNotFoundError: No module named 'django'` | 가상환경 활성화 안 함. `.\.venv\Scripts\Activate.ps1` 후 `pip install -r requirements.txt` |
| `no such table: django_session` (로그인 시 오류) | `python manage.py migrate` 를 실행하지 않음 |
| `Error: That port is already in use.` | 다른 포트로 실행: `python manage.py runserver 8001` |
| `Activate.ps1 ... 실행할 수 없습니다` | 위의 `Set-ExecutionPolicy` 실행 |
| pip 설치 중 빌드 오류 | Python 3.13 초과 버전 사용 중일 수 있음. 3.12 설치 권장 |

동작 확인용 스모크 테스트:

```bash
python manage.py test
```

---

## 5. 구조

```
apps/
  accounts/    로그인 / 체험 로그인 / Face 인증 / 세션 권한
  dashboard/   Dashboard
  projects/    Project List / Detail / Chatbot
  management/  Tasks / Agents / Results (관리자)
  comingsoon/  Coming Soon (파일 기반 Markdown 문서)
apps/mockdata.py      화면용 임시 데이터 (Backend 연동 시 교체)
content/coming_soon/  Coming Soon 문서 (삭제 시 deleted 폴더로 이동)
templates/, static/   화면 및 공통 스타일
```

## 6. 화면

| 영역 | 경로 |
| --- | --- |
| Login | `/login/`, `/login/demo/`, `/login/face/` |
| Dashboard | `/` |
| Projects | `/projects/`, `/projects/<id>/` |
| Tasks 관리 | `/manage/tasks/` |
| Agents 관리 | `/manage/agents/`, `/manage/agents/<key>/` |
| Results 관리 | `/manage/results/` |
| Coming Soon | `/coming-soon/`, `/coming-soon/manage/` |

## 7. 현재 범위

- 화면과 흐름만 구현. 데이터는 `apps/mockdata.py` 의 임시 데이터.
- 실제 Google OAuth / 얼굴 인식 / MySQL / LLM / RAG 연동은 다음 단계.
- Coming Soon 문서만 실제 파일(`content/coming_soon/*.md`)로 저장·수정·삭제된다.
