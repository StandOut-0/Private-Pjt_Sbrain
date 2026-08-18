@echo off
REM Second Brain 개발 서버 실행 (Windows)
REM 가상환경 생성 -> 패키지 설치 -> DB 준비 -> 서버 실행 까지 한 번에 처리한다.

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python 이 설치되어 있지 않거나 PATH 에 없습니다.
  echo         https://www.python.org/downloads/windows/ 에서 설치 후
  echo         "Add python.exe to PATH" 를 체크하고 터미널을 새로 열어주세요.
  pause
  exit /b 1
)

if not exist ".venv" (
  echo [1/4] 가상환경 생성 중...
  python -m venv .venv || (echo [ERROR] 가상환경 생성 실패 & pause & exit /b 1)
)

echo [2/4] 패키지 설치 중...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
call ".venv\Scripts\python.exe" -m pip install -r requirements.txt || (echo [ERROR] 패키지 설치 실패 & pause & exit /b 1)

echo [3/4] 데이터베이스 준비 중...
call ".venv\Scripts\python.exe" manage.py migrate || (echo [ERROR] migrate 실패 & pause & exit /b 1)

echo [4/4] 서버 실행: http://127.0.0.1:8000/login/  (종료: Ctrl + C)
call ".venv\Scripts\python.exe" manage.py runserver
pause
