#!/usr/bin/env python3
"""VSCode에서 사용 중인 Python 환경과 pykrx 설치 상태 확인"""

import sys
import subprocess

print("=" * 80)
print("Python 환경 정보")
print("=" * 80)
print(f"Python 실행 파일: {sys.executable}")
print(f"Python 버전: {sys.version}")
print(f"Python 경로들: {sys.path[:3]}")
print()

print("=" * 80)
print("pykrx 설치 상태 확인")
print("=" * 80)

try:
    import pykrx
    print(f"✅ pykrx 설치됨")
    print(f"   버전: {pykrx.__version__}")
    print(f"   위치: {pykrx.__file__}")
except ImportError as e:
    print(f"❌ pykrx 설치 안 됨")
    print(f"   오류: {e}")
    print()
    print("해결 방법:")
    print(f"   {sys.executable} -m pip install pykrx>=1.0.40")

print()
print("=" * 80)
print("설치된 패키지 목록 (pykrx 관련)")
print("=" * 80)
try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list"],
        capture_output=True,
        text=True
    )
    for line in result.stdout.split('\n'):
        if 'pykrx' in line.lower():
            print(line)
except Exception as e:
    print(f"패키지 목록 조회 실패: {e}")
