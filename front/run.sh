#!/usr/bin/env bash
# Second Brain 개발 서버 실행 (macOS / Linux)
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 가 설치되어 있지 않습니다."
  exit 1
fi

[ -d .venv ] || python3 -m venv .venv

.venv/bin/python -m pip install --upgrade pip >/dev/null
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate

echo "서버 실행: http://127.0.0.1:8000/login/  (종료: Ctrl + C)"
.venv/bin/python manage.py runserver
