#!/usr/bin/env python
"""MCP 서버 테스트 스크립트"""
import sys
import subprocess

print("=" * 60)
print("MCP 서버 연결 테스트")
print("=" * 60)

# 1. Python 버전 확인
print(f"\n1. Python 버전: {sys.version}")
print(f"   Python 경로: {sys.executable}")

# 2. 필수 패키지 확인
required_packages = ['mcp', 'pykrx', 'pandas', 'numpy']
print("\n2. 필수 패키지 확인:")
for pkg in required_packages:
    try:
        __import__(pkg)
        print(f"   ✓ {pkg}")
    except ImportError:
        print(f"   ✗ {pkg} (설치 필요!)")

# 3. mcp_server.py 구문 검사
print("\n3. mcp_server.py 구문 검사:")
result = subprocess.run(
    [sys.executable, "-m", "py_compile", "mcp_server.py"],
    capture_output=True,
    text=True
)
if result.returncode == 0:
    print("   ✓ 구문 오류 없음")
else:
    print(f"   ✗ 구문 오류: {result.stderr}")

# 4. MCP 서버 실행 테스트 (5초)
print("\n4. MCP 서버 실행 테스트 (5초):")
print("   서버 시작 중...")
try:
    result = subprocess.run(
        [sys.executable, "mcp_server.py"],
        timeout=5,
        capture_output=True,
        text=True
    )
    print("   ✗ 서버가 5초 내에 종료됨 (비정상)")
    if result.stdout:
        print(f"   stdout: {result.stdout[:200]}")
    if result.stderr:
        print(f"   stderr: {result.stderr[:200]}")
except subprocess.TimeoutExpired:
    print("   ✓ 서버가 정상적으로 실행 중 (timeout은 정상)")

# 5. 권장 설정
print("\n" + "=" * 60)
print("권장 Claude Desktop 설정:")
print("=" * 60)
print('''
{
  "mcpServers": {
    "finance-market": {
      "command": "python",
      "args": [
        "/home/user/finance-market/mcp_server.py"
      ]
    }
  }
}

또는 (uv 사용):

{
  "mcpServers": {
    "finance-market": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/home/user/finance-market",
        "python",
        "mcp_server.py"
      ]
    }
  }
}
''')

print("\n" + "=" * 60)
print("문제 해결 팁:")
print("=" * 60)
print("""
1. Claude Desktop을 완전히 종료하고 다시 시작
2. 설정 파일 위치:
   - Windows: %APPDATA%\\Claude\\claude_desktop_config.json
   - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
3. 로그 확인:
   - Windows: %APPDATA%\\Claude\\logs
   - macOS: ~/Library/Logs/Claude
4. 설정 파일에서 JSON 문법 오류 확인 (콤마, 중괄호 등)
5. Python 경로가 절대 경로인지 확인
""")
