import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django를 가져올 수 없습니다. Django가 설치되어 있고 "
            "PYTHONPATH 환경 변수에서 사용할 수 있는지 확인해 보세요. "
            "가상 환경을 활성화하는 것을 잊으셨나요?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
