"""
PyInstaller를 사용하여 독립 실행 파일 생성
"""
# 사용법:
# pip install pyinstaller
# python build_exe.py

import PyInstaller.__main__
import os

# 프로젝트 루트 경로
project_root = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    'mcp_server.py',
    '--onefile',
    '--name=finance-market-mcp',
    '--hidden-import=mcp',
    '--hidden-import=numpy',
    '--hidden-import=pandas',
    '--hidden-import=scipy',
    '--hidden-import=pykrx',
    '--collect-all=mcp',
    f'--add-data={project_root}/src;src',
    '--clean',
])

print("\n✅ 실행 파일 생성 완료!")
print("📁 위치: dist/finance-market-mcp.exe")
