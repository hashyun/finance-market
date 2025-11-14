# ⚡ 빠른 설치 가이드

## 방법 1: uv 자동 설치 (권장) 🚀

### 1. uv 설치

**Windows (PowerShell):**
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**또는 pip:**
```bash
pip install uv
```

### 2. Claude Desktop 설정

`claude_desktop_config.json` 파일에 추가:

**Windows 경로 예시:**
```json
{
  "mcpServers": {
    "finance-market": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "C:\\github\\finance-market",
        "python",
        "mcp_server.py"
      ],
      "env": {
        "FRED_API_KEY": "선택사항",
        "ECOS_API_KEY": "선택사항",
        "DART_API_KEY": "선택사항"
      }
    }
  }
}
```

**macOS/Linux 경로 예시:**
```json
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
      ],
      "env": {
        "FRED_API_KEY": "선택사항",
        "ECOS_API_KEY": "선택사항",
        "DART_API_KEY": "선택사항"
      }
    }
  }
}
```

### 3. Claude Desktop 재시작

완료! 🎉 의존성이 자동으로 설치됩니다.

---

## 방법 2: 수동 설치

### 1. 패키지 설치

```bash
cd C:\github\finance-market  # 본인 경로
pip install -r requirements.txt
```

### 2. Claude Desktop 설정

```json
{
  "mcpServers": {
    "finance-market": {
      "command": "python",
      "args": ["C:\\github\\finance-market\\mcp_server.py"],
      "env": {
        "FRED_API_KEY": "선택사항",
        "ECOS_API_KEY": "선택사항",
        "DART_API_KEY": "선택사항"
      }
    }
  }
}
```

---

## 방법 3: GitHub에서 직접 실행

```json
{
  "mcpServers": {
    "finance-market": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/hashyun/finance-market.git@claude/mcp-implementation-01Xdf2KBFz5Q2u2FjQ6yNMUg",
        "python",
        "mcp_server.py"
      ],
      "env": {
        "FRED_API_KEY": "선택사항",
        "ECOS_API_KEY": "선택사항",
        "DART_API_KEY": "선택사항"
      }
    }
  }
}
```

---

## 🔑 API 키 (모두 선택사항)

- **FRED**: https://fred.stlouisfed.org/docs/api/api_key.html
- **ECOS**: https://ecos.bok.or.kr/api/#/
- **DART**: https://opendart.fss.or.kr/

API 키 없이도 포트폴리오 분석/최적화는 사용 가능합니다!

---

## ✅ 설정 파일 위치

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

---

## 🎯 사용 예시

Claude Desktop에서:

```
"삼성전자 40%, SK하이닉스 30%, NAVER 30%로 구성된 포트폴리오를 분석해줘"

"이 종목들로 최적 포트폴리오를 만들어줘"

"미국 10년 국채 수익률을 조회해줘"
```

---

## 🐛 문제 해결

### uv를 찾을 수 없음
```bash
# PATH 재설정 또는 재부팅 후 다시 시도
```

### 여전히 패키지 오류
```bash
# 프로젝트 폴더에서 직접 설치
cd C:\github\finance-market
uv pip install -r requirements.txt
```

자세한 내용은 [MCP_SETUP.md](MCP_SETUP.md)를 참조하세요.
