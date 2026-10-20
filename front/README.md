# Second Brain

## 사용자 가이드

사이드바 맨 아래 사용자 가이드 메뉴에서 샘플 PDF 뷰어를 새 탭으로 열 수 있습니다.
PDF가 없거나 확인할 수 없는 경우에는 `준비 중`으로 표시하며 링크를 제공하지 않습니다.
향후 실제 화면을 담은 PDF를 `static/docs/user-guide.pdf`에 등록하면, 사용자 가이드 메뉴를 열 때 파일을 확인하여 새 탭으로 여는 버튼을 표시합니다.
샘플 PDF가 포함되어 있으며 정식 가이드로 교체할 수 있습니다. 뷰어는 `static/docs/user-guide-viewer.html`이며 PDF 직접 열기와 다운로드를 제공합니다.

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

### 환경 설정

로컬 개발은 `DJANGO_DEBUG=1`을 기본으로 사용합니다. Django 첫 실행 때 개발용 `SECRET_KEY`를 `front/.local-django-secret`에 생성하며 이 파일은 Git에 포함되지 않습니다. 개발 서버는 `127.0.0.1` 또는 `localhost`로 접속하세요.

운영 배포 전에는 서버 환경에 아래 값을 설정해야 합니다. `DJANGO_DEBUG=0`인데 `DJANGO_SECRET_KEY`가 없으면 Django가 시작되지 않습니다. `DJANGO_ALLOWED_HOSTS`에는 실제 서비스 호스트만 쉼표로 구분해 입력하세요. `.env` 파일을 자동으로 읽는 설정은 사용하지 않으므로 비밀값은 배포 환경의 환경변수/Secret 기능으로 주입합니다.

| 변수 | 로컬 기본값 | 운영 설정 |
| --- | --- | --- |
| `DJANGO_DEBUG` | `1` | `0` 필수 |
| `DJANGO_SECRET_KEY` | 저장소 밖에 생성 | 안전한 임의 값 필수 |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost,testserver` | 실제 호스트만 지정 |


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
