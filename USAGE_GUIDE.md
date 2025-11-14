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

**find_foreign_favorites** - 외국인 선호 종목 발굴 (실제 데이터 분석)
- 대형주 15개 또는 KOSPI 시가총액 상위 100개 분석
- 거래량(30%) + 외국인(40%) + 기관(30%) 종합 점수 계산
- run_portfolio.py와 동일한 로직으로 상위 종목 추천

**get_trading_signals** - 다중 전략 매매 신호 (실시간 분석)
- 외국인 추종: 외국인+기관 순매수 동향 분석
- 모멘텀: 이동평균선 정배열/역배열 확인
- 거래량: 거래량 급증/감소 패턴 감지
- 3개 전략 종합 판단 (🟢매수/🔴매도/🟡관망)

**analyze_short_squeeze** - 숏 스퀴즈 가능성 분석 (공매도 데이터 기반)
- pykrx 공매도 잔고 데이터 실시간 조회
- 공매도 비율 + 외국인/기관 매수세 교차 분석
- 위험도 점수(0-100점) 산출 및 급등 가능성 평가

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
대형주 15개 중에서 외국인이 가장 많이 매수한 종목 5개 찾아줘
또는
KOSPI 시가총액 상위 100개를 분석해서 상위 10개 추천해줘
```

### 예시 3: 다중 전략 매매 신호
```
삼성전자 매매 신호 분석해줘
(외국인추종, 모멘텀, 거래량 전략 종합 분석)
```

### 예시 4: 숏 스퀴즈 후보 분석
```
카카오 숏 스퀴즈 가능성 분석해줘
(공매도 잔고 + 외국인/기관 매수세 분석)
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

### 외국인 선호 종목 분석 (find_foreign_favorites)
대형주 또는 KOSPI 시가총액 상위 종목들을 종합 분석:
- **거래량(30%)**: 시장에서 활발히 거래되는 종목
- **외국인 순매수(40%)**: 외국인 매수 강도 (가중치 최대)
- **기관 순매수(30%)**: 기관 투자자 선호도
- run_portfolio.py와 동일한 검증된 알고리즘 사용
- 삼성전자만 추천되는 문제 해결 → 다양한 종목 추천

### 다중 전략 매매 신호 (get_trading_signals)
3가지 전략을 종합하여 객관적 판단:
1. **외국인 추종**: 외국인+기관 동시 매수/매도 확인
2. **모멘텀**: MA5 > MA20 > MA60 정배열 체크
3. **거래량**: 평균 대비 1.5배 이상 급증 감지
- 2개 이상 전략이 일치하면 매수/매도 신호
- 불일치 시 관망 권장

### 숏 스퀴즈 분석 (analyze_short_squeeze)
공매도 데이터 기반 실전 분석:
- **공매도 비율**: 거래량 대비 20% 이상 시 고위험
- **외국인/기관 매수**: 동시 순매수 전환 시 압박 강화
- **거래량 급증**: 평균 대비 1.5배 이상 시 청산 압력
- **위험도 점수**: 0-100점 산출하여 객관적 평가

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
