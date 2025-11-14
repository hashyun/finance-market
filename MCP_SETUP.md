# MCP 서버 설정 가이드

## Claude Desktop과 연동하기

이 프로젝트를 MCP(Model Context Protocol) 서버로 Claude Desktop에 연동하는 방법입니다.

## 1. 사전 준비

### 필수 패키지 설치

```bash
pip install -r requirements.txt
```

### API 키 발급

다음 API 키들을 발급받으세요:

1. **FRED API 키** (선택사항, 미국 경제 데이터)
   - 발급: https://fred.stlouisfed.org/docs/api/api_key.html
   - 무료

2. **ECOS API 키** (선택사항, 한국은행 경제통계)
   - 발급: https://ecos.bok.or.kr/api/#/
   - 무료, 회원가입 필요

3. **DART API 키** (선택사항, 기업 공시정보)
   - 발급: https://opendart.fss.or.kr/
   - 무료, 회원가입 필요

### 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 API 키를 입력하세요:

```bash
# .env 파일 생성
cp .env.example .env
```

`.env` 파일 내용:

```env
# FRED API 키 (미국 경제 데이터)
FRED_API_KEY=your_fred_api_key_here

# ECOS API 키 (한국은행 경제통계)
ECOS_API_KEY=your_ecos_api_key_here

# DART API 키 (기업 공시정보)
DART_API_KEY=your_dart_api_key_here
```

> **참고**: API 키가 없어도 일부 기능(포트폴리오 분석, 국채 수익률 등)은 사용 가능합니다.

## 2. Claude Desktop 설정

### macOS

Claude Desktop 설정 파일 위치:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Windows

Claude Desktop 설정 파일 위치:
```
%APPDATA%\Claude\claude_desktop_config.json
```

### 설정 파일 편집

위 경로의 `claude_desktop_config.json` 파일을 열고 다음 내용을 추가하세요:

```json
{
  "mcpServers": {
    "finance-market": {
      "command": "python",
      "args": [
        "/절대/경로/finance-market/mcp_server.py"
      ],
      "env": {
        "FRED_API_KEY": "your_fred_api_key_here",
        "ECOS_API_KEY": "your_ecos_api_key_here",
        "DART_API_KEY": "your_dart_api_key_here"
      }
    }
  }
}
```

> **중요**: `/절대/경로/finance-market/mcp_server.py`를 실제 프로젝트 경로로 변경하세요.

예시 (macOS/Linux):
```json
{
  "mcpServers": {
    "finance-market": {
      "command": "python",
      "args": [
        "/Users/yourname/projects/finance-market/mcp_server.py"
      ],
      "env": {
        "FRED_API_KEY": "abc123...",
        "ECOS_API_KEY": "xyz789...",
        "DART_API_KEY": "def456..."
      }
    }
  }
}
```

## 3. Claude Desktop 재시작

설정 파일을 저장한 후 Claude Desktop을 완전히 종료하고 다시 시작하세요.

## 4. 사용 가능한 도구

MCP 서버가 성공적으로 연동되면 Claude Desktop에서 다음 도구들을 사용할 수 있습니다:

### 1. 포트폴리오 리스크 분석 (`analyze_portfolio_risk`)

포트폴리오의 시장 리스크, 신용 리스크, 유동성 리스크를 종합 분석합니다.

**사용 예시**:
```
내 포트폴리오를 분석해줘:
- 삼성전자 (005930): 40%
- SK하이닉스 (000660): 30%
- NAVER (035420): 30%
```

### 2. 포트폴리오 최적화 (`optimize_portfolio`)

주어진 주식들로 최적 포트폴리오를 구성합니다.

**사용 예시**:
```
다음 종목들로 샤프 비율을 최대화하는 포트폴리오를 만들어줘:
- 삼성전자, SK하이닉스, NAVER, 카카오
```

### 3. FRED 데이터 조회 (`get_fred_data`)

미국 경제 지표를 조회합니다.

**사용 예시**:
```
미국 국채 수익률 곡선을 보여줘
최근 1년간 연방기금금리 추이를 보여줘
```

### 4. ECOS 데이터 조회 (`get_ecos_data`)

한국은행 경제통계를 조회합니다.

**사용 예시**:
```
한국의 기준금리 추이를 보여줘
최근 환율 데이터를 조회해줘
```

### 5. 기업정보 조회 (`get_company_info`)

DART를 통해 기업 재무정보를 조회합니다.

**사용 예시**:
```
삼성전자의 재무비율을 보여줘
현대차의 최근 공시 목록을 조회해줘
```

### 6. 국채 수익률 조회 (`get_bond_yields`)

한국 국채 수익률 곡선을 조회하고 분석합니다.

**사용 예시**:
```
현재 국채 수익률 곡선을 보여줘
10년-1년 국채 스프레드 추이를 분석해줘
```

## 5. 문제 해결

### MCP 서버가 인식되지 않는 경우

1. **Python 경로 확인**
   ```bash
   which python
   # 또는
   which python3
   ```

   설정 파일의 `command`를 실제 Python 경로로 변경:
   ```json
   "command": "/usr/local/bin/python3"
   ```

2. **절대 경로 확인**
   ```bash
   pwd
   ```

   현재 프로젝트의 절대 경로를 확인하고 설정 파일에 정확히 입력

3. **Claude Desktop 로그 확인**
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`

### API 키 오류

API 키가 없는 경우 일부 도구만 작동합니다:

- **API 키 불필요**: `analyze_portfolio_risk`, `optimize_portfolio`, `get_bond_yields`
- **FRED API 필요**: `get_fred_data`
- **ECOS API 필요**: `get_ecos_data`
- **DART API 필요**: `get_company_info`

### 패키지 설치 오류

```bash
# 가상환경 사용 권장
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

## 6. 고급 설정

### 가상환경 사용

프로젝트별 Python 환경을 분리하려면:

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows

# 패키지 설치
pip install -r requirements.txt
```

Claude Desktop 설정 파일에서 가상환경의 Python을 사용:

```json
{
  "mcpServers": {
    "finance-market": {
      "command": "/절대/경로/finance-market/venv/bin/python",
      "args": [
        "/절대/경로/finance-market/mcp_server.py"
      ],
      "env": {
        "FRED_API_KEY": "...",
        "ECOS_API_KEY": "...",
        "DART_API_KEY": "..."
      }
    }
  }
}
```

### 환경변수 파일 사용

`.env` 파일을 사용하는 경우 설정 파일에서 `env`를 제거할 수 있습니다:

```json
{
  "mcpServers": {
    "finance-market": {
      "command": "python",
      "args": [
        "/절대/경로/finance-market/mcp_server.py"
      ]
    }
  }
}
```

## 7. 테스트

MCP 서버를 직접 실행하여 테스트:

```bash
python mcp_server.py
```

오류 없이 실행되면 Claude Desktop에서도 작동합니다.

## 8. 지원

문제가 발생하면 다음을 확인하세요:

1. Python 버전 (3.8 이상)
2. 모든 패키지가 설치되었는지
3. API 키가 올바른지
4. 절대 경로가 정확한지
5. Claude Desktop이 최신 버전인지

자세한 내용은 프로젝트 README.md를 참조하세요.
