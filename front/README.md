# Second Brain

1. 각자의 email을 알려주세요 아래의 서식에 액세스 권한을 추가해드릴게요.
https://docs.google.com/presentation/d/1PPc6K-sohMQHhVlUIuqCL0WABpazmrAc/edit?usp=sharing&ouid=114041644283327531753&rtpof=true&sd=true



## S brain - front - Scaffolding 
#### PSH(standout) - 26.08.25 ----- start
1. 터미널에 명령하세요   .\run.bat
2. http://127.0.0.1:8000/login에 접속해 체험 로그인(SECONDBRAIN)하세요.
3. python manage.py createsuperuser 명령해 관리자 계정을 만들고, http://127.0.0.1:8000/django-admin/에 접속해 관리자 로그인 하세요. 

 현재 화면과 흐름만 구현되었고, 데이터는 `apps/mockdata.py` 의 임시 데이터를 사용합니다.<br>
Coming Soon 문서는 실제 파일(`content/coming_soon/*.md`)로 저장·수정·삭제되요. 구현 전중후 좋은 아이디어가 있으실 경우 sample.md 문서 복제해서 작성후 push한 뒤 구성원과 공유해주세요.
#### PSH(standout) - 26.08.25 ----- end
---

#### SAMPLE(sample) - 26.00.00 ----- start
#### SAMPLE(sample) - 26.00.00 ----- end
---




<br><br><br><br><br>
## 1. Python **3.10 ~ 3.13**

Python이 없다면 https://www.python.org/downloads/windows에서 설치하거나 명령하세요. 

설치 후 IDE를 재부팅하거나 **터미널(PowerShell)을 새로 열어야** `python` 명령이 인식되니 확인하세요.

Windows에서 `python`을 치면 Microsoft Store가 열리는 경우, 설정 → 앱 → 앱 실행 별칭 → `python.exe` / `python3.exe` 를 끄세요.
```powershell
python --version
winget install -e --id Python.Python.3.12
```
- macOS: `brew install python@3.12`
- Ubuntu: `sudo apt install python3 python3-venv python3-pip`



## 2. 실행
`run.bat` 혹은 `.\run.bat`(macOS / Linux: `bash run.sh`) 명령하세요.

가상환경 생성 → 패키지 설치 → DB 준비 → 서버 실행까지 자동으로 진행됩니다.

문제가 지속될 경우 수동실행을 수행하세요.
```powershell
cd "C:\Users\Dell XPS 13\Desktop\sh\front\front\second-brain"

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

```bash
cd second-brain
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```


## 3. 로그인
브라우저에서 <http://127.0.0.1:8000/login/> 접속하세요.

`Activate.ps1` 실행이 차단되면(실행 정책 오류) Set-ExecutionPolicy -Scope CurrentUser RemoteSigned 명령 뒤 다시 시도하세요.
|  |  |
| --- | --- |
| 일반 사용자 | `Google로 로그인` 버튼 (실제 OAuth 아님) |
| 관리자 | `관리자로 로그인` → Face 인증 화면 → `얼굴 인증` 버튼 |
| 체험 | `체험 로그인` → 인증 코드 `SECONDBRAIN` |


## 4. 자주 나는 오류

| 증상 | 해결 |
| --- | --- |
| `'python'은(는) 내부 또는 외부 명령...` | Python 미설치 또는 PATH 미등록. 0번 항목 참고 후 터미널 재시작 |
| `ModuleNotFoundError: No module named 'django'` | 가상환경 활성화 안 함. `.\.venv\Scripts\Activate.ps1` 후 `pip install -r requirements.txt` |
| `no such table: django_session` (로그인 시 오류) | `python manage.py migrate` 를 실행하지 않음 |
| `Error: That port is already in use.` | 다른 포트로 실행: `python manage.py runserver 8001` |
| `Activate.ps1 ... 실행할 수 없습니다` | 위의 `Set-ExecutionPolicy` 실행 |
| pip 설치 중 빌드 오류 | Python 3.13 초과 버전 사용 중일 수 있음. 3.12 설치 권장 |


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
| Tasks  | `/manage/tasks/` |
| Agents | `/manage/agents/`, `/manage/agents/<key>/` |
| Results | `/manage/results/` |
| Coming Soon | `/coming-soon/`, `/coming-soon/manage/` |
