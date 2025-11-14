# 📖 Finance Market MCP 사용 가이드

## ✨ 구현된 기능

### 1. 간편 포트폴리오 분석 (자연어 입력)

**analyze_my_portfolio** - 보유 종목을 자연어로 입력하여 바로 분석
```
"삼성전자 100주, SK하이닉스 50주, NAVER 30주"
```

**optimize_my_stocks** - 보유 종목으로 최적 포트폴리오 생성
```
"삼성전자, SK하이닉스, NAVER, 카카오"
```

**get_stock_info** - 실시간 종목 정보 조회
```
"005930" 또는 "삼성전자"
```

### 2. 한국 시장 투자자 분석 ⭐ NEW

**get_investor_flow** - 투자자별 매매 동향 분석
- 외국인, 기관, 개인 투자자의 순매수/순매도 추세
- 투자 심리 파악 및 시장 방향성 예측

**find_foreign_favorites** - 외국인 선호 종목 발굴
- 외국인 매수세가 강한 종목 찾기
- 외국인 비중 및 순매수 강도 분석

**get_trading_signals** - 다중 전략 매매 신호
- Foreign Follow: 외국인 매매 추종 전략
- Momentum: 모멘텀 전략
- Mean Reversion: 평균 회귀 전략

**analyze_short_squeeze** - 숏 스퀴즈 가능성 분석
- 공매도 잔고 vs 외국인/기관 매수세 비교
- 급등 가능성 있는 종목 발굴

### 3. 고급 리스크 분석

**analyze_portfolio_risk** - 통합 리스크 분석
- 시장 리스크: VaR, CVaR, Beta, Sharpe Ratio
- 신용 리스크: 부채비율, 유동비율, 신용등급
- 유동성 리스크: 거래량, 시가총액

**optimize_portfolio** - 포트폴리오 최적화
- Sharpe Ratio 최대화
- 리스크 제약 조건 적용

### 4. 경제 데이터 조회

**get_fred_data** - FRED 경제 지표
- 미국 국채 수익률, GDP, 실업률 등

**get_ecos_data** - 한국은행 경제통계
- 한국 기준금리, GDP, 통화량 등

**get_bond_yields** - 한국 국채 수익률
- 수익률 곡선 조회

**get_company_info** - 기업 재무 정보
- DART 공시 데이터

---

## 🎯 Claude Desktop 사용 예시

### 예시 1: 보유 종목 빠른 분석
```
내 포트폴리오 분석해줘:
삼성전자 100주, SK하이닉스 50주, NAVER 30주
```

### 예시 2: 외국인이 사는 종목 찾기
```
최근 1개월간 외국인이 가장 많이 매수한 종목 10개 찾아줘
```

### 예시 3: 다중 전략 매매 신호
```
삼성전자에 대한 외국인추종, 모멘텀, 평균회귀 전략 신호를 모두 보여줘
```

### 예시 4: 숏 스퀴즈 후보 찾기
```
공매도 잔고가 높은데 외국인이 계속 사고 있는 종목 있어?
```

### 예시 5: 포트폴리오 최적화
```
삼성전자, SK하이닉스, NAVER, 카카오, 현대차로
샤프비율이 최대가 되는 포트폴리오를 만들어줘
```

### 예시 6: 시장 리스크 분석
```
내 포트폴리오의 VaR과 CVaR을 계산해줘
시장 폭락 시 얼마나 손실날 수 있는지 알고 싶어
```

### 예시 7: 경제 지표 확인
```
미국 10년 국채 수익률 최근 추세 보여줘
```

---

## 🔧 설정 방법

### 1. Claude Desktop 설정 파일 위치

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

### 2. 권장 설정 (uv 자동 설치)

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

### 3. 대체 설정 (자동 패키지 설치)

```json
{
  "mcpServers": {
    "finance-market": {
      "command": "python",
      "args": ["/home/user/finance-market/mcp_server_auto.py"],
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

API 키가 없어도 **한국 주식 분석, 투자자 동향, 포트폴리오 최적화**는 모두 사용 가능합니다!

API 키는 추가 경제 데이터 조회에만 필요:

- **FRED**: https://fred.stlouisfed.org/docs/api/api_key.html
  - 미국 경제 지표 조회 시 필요

- **ECOS**: https://ecos.bok.or.kr/api/#/
  - 한국은행 경제통계 조회 시 필요

- **DART**: https://opendart.fss.or.kr/
  - 기업 재무제표 상세 조회 시 필요

---

## 📊 주요 기능 상세

### 투자자 동향 분석
외국인, 기관, 개인의 매매 패턴을 분석하여:
- 시장 주도 세력 파악
- 투자 심리 변화 감지
- 수급 기반 매매 타이밍 포착

### 외국인 추종 전략
외국인 투자자가 지속적으로 매수하는 종목:
- 펀더멘털이 우수한 종목일 가능성
- 중장기 상승 모멘텀 기대

### 숏 스퀴즈 분석
공매도 잔고가 높은 상태에서:
- 외국인/기관이 순매수 시작
- 공매도 세력의 강제 청산 가능성
- 급격한 주가 상승 기회 포착

### 리스크 관리
- **VaR/CVaR**: 최악의 시나리오에서 예상 손실
- **Beta**: 시장 대비 변동성
- **Sharpe Ratio**: 위험 대비 수익률

---

## 🚀 시작하기

1. **설정 파일 수정**: 위 설정을 복사하여 본인 경로로 변경
2. **Claude Desktop 재시작**
3. **채팅 시작**: "내 포트폴리오 분석해줘: 삼성전자 100주"

더 자세한 내용은 `QUICK_SETUP.md`를 참조하세요!
