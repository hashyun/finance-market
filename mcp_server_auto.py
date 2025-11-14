#!/usr/bin/env python3
"""
Finance Market Analysis MCP Server (자동 설치 버전)
필요한 패키지를 자동으로 설치합니다
"""
import sys
import subprocess
import importlib.util

def ensure_package(package_name, import_name=None):
    """패키지가 없으면 자동 설치"""
    if import_name is None:
        import_name = package_name

    if importlib.util.find_spec(import_name) is None:
        print(f"📦 {package_name} 설치 중...", file=sys.stderr)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package_name])
        print(f"✅ {package_name} 설치 완료", file=sys.stderr)

# 필수 패키지 자동 설치
required_packages = [
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("scipy", "scipy"),
    ("requests", "requests"),
    ("pykrx", "pykrx"),
    ("mcp", "mcp"),
    ("python-dotenv", "dotenv"),
]

print("🚀 필요한 패키지 확인 중...", file=sys.stderr)
for pkg, import_name in required_packages:
    ensure_package(pkg, import_name)

# 선택적 패키지 (오류 무시)
optional_packages = [
    ("fredapi", "fredapi"),
    ("lxml", "lxml"),
    ("beautifulsoup4", "bs4"),
]

for pkg, import_name in optional_packages:
    try:
        ensure_package(pkg, import_name)
    except:
        print(f"⚠️  {pkg} 설치 실패 (선택사항)", file=sys.stderr)

print("✨ 모든 패키지 준비 완료!", file=sys.stderr)

# 이제 실제 MCP 서버 실행
from mcp_server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
