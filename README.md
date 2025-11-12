# 한국 주식 포트폴리오 위험 관리 시스템

Market Risk, Credit Risk, Liquidity Risk를 종합적으로 고려한 스마트 포트폴리오 구성 시스템입니다.

## 주요 기능

### 1. 시장 위험(Market Risk) 관리
- **VaR (Value at Risk)**: 특정 신뢰수준에서의 최대 예상 손실
- **CVaR (Conditional VaR)**: VaR을 초과하는 손실의 평균
- **베타(β)**: 시장 대비 개별 주식의 민감도
- **최대 낙폭(Maximum Drawdown)**: 최고점 대비 최대 하락폭
- **분산투자 비율**: 포트폴리오의 분산 효과 측정

### 2. 신용 위험(Credit Risk) 관리
- **신용 점수**: 신용등급, 부채비율, 유동비율 종합 평가
- **부채비율 분석**: 기업의 부채 대비 자기자본 비율
- **유동비율 분석**: 단기 부채 상환 능력
- **집중 위험(HHI)**: 특정 종목/섹터 집중도 측정
- **섹터별 노출도**: 업종별 투자 비중 분석

### 3. 유동성 위험(Liquidity Risk) 관리
- **거래량 분석**: 일평균 거래량 기반 유동성 평가
- **시가총액 분석**: 대형주/중형주/소형주 분류
- **청산 소요 시간**: 포지션 청산에 필요한 예상 시간
- **유동성 조정 VaR**: 유동성을 고려한 위험 평가

### 4. 포트폴리오 최적화
- **샤프 비율 최대화**: 전통적인 위험 대비 수익률 최적화
- **위험 인식 최적화**: 세 가지 위험을 통합하여 최적화
- **효율적 투자선**: 다양한 위험-수익률 조합 생성
- **종합 위험 점수**: 통합 위험 관리 지표

## 설치 방법

### 필수 요구사항
- Python 3.8 이상
- pip 패키지 관리자

### 의존성 설치

```bash
pip install -r requirements.txt
```

필요한 패키지:
- numpy: 수치 계산
- pandas: 데이터 처리
- scipy: 최적화 알고리즘
- matplotlib: 시각화 (선택사항)

## 프로젝트 구조

```
finance-market/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   └── stock.py              # Stock, Portfolio 클래스
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── market_risk.py        # 시장 위험 분석
│   │   ├── credit_risk.py        # 신용 위험 분석
│   │   └── liquidity_risk.py     # 유동성 위험 분석
│   ├── portfolio/
│   │   ├── __init__.py
│   │   └── optimizer.py          # 포트폴리오 최적화
│   └── utils/
│       ├── __init__.py
│       └── data_loader.py        # 데이터 로딩
├── examples/
│   └── portfolio_example.py      # 사용 예제
├── data/
│   └── sample_stocks.json        # 샘플 데이터
├── requirements.txt
└── README.md
```

## 사용 방법

### 기본 예제 실행

```bash
cd examples
python portfolio_example.py
```

### 사용자 정의 포트폴리오 구성

```python
from src.utils.data_loader import DataLoader
from src.portfolio.optimizer import PortfolioOptimizer

# 1. 데이터 로드
stocks = DataLoader.load_from_json('data/sample_stocks.json')

# 2. 최적화 엔진 생성
optimizer = PortfolioOptimizer(
    stocks=stocks,
    risk_free_rate=0.03,
    market_risk_weight=0.4,
    credit_risk_weight=0.3,
    liquidity_risk_weight=0.3
)

# 3. 위험 인식 포트폴리오 최적화
portfolio = optimizer.optimize_risk_aware(
    min_credit_score=40.0,
    min_liquidity_score=40.0
)

# 4. 분석 결과 확인
analysis = optimizer.analyze_portfolio(portfolio)
print(f"기대 수익률: {analysis['expected_return']:.2%}")
print(f"변동성: {analysis['volatility']:.2%}")
print(f"샤프 비율: {analysis['sharpe_ratio']:.2f}")
print(f"신용 점수: {analysis['credit_score']:.1f}/100")
print(f"유동성 점수: {analysis['liquidity_score']:.1f}/100")
```

### 개별 위험 분석

```python
from src.models.stock import Stock, Portfolio
from src.risk.market_risk import MarketRiskAnalyzer
from src.risk.credit_risk import CreditRiskAnalyzer
from src.risk.liquidity_risk import LiquidityRiskAnalyzer

# 포트폴리오 생성
portfolio = Portfolio(stocks, weights=[0.2, 0.3, 0.5])

# 시장 위험 분석
var_95 = MarketRiskAnalyzer.value_at_risk(portfolio, confidence_level=0.95)
cvar_95 = MarketRiskAnalyzer.conditional_var(portfolio, confidence_level=0.95)

# 신용 위험 분석
credit_score = CreditRiskAnalyzer.portfolio_credit_score(portfolio)
sector_exposure = CreditRiskAnalyzer.sector_exposure(portfolio)

# 유동성 위험 분석
liquidity_score = LiquidityRiskAnalyzer.portfolio_liquidity_score(portfolio)
liquidation_time = LiquidityRiskAnalyzer.portfolio_liquidation_time(
    portfolio,
    portfolio_value=100_000_000
)
```

## 데이터 형식

주식 데이터는 JSON 형식으로 제공되어야 합니다:

```json
[
  {
    "ticker": "005930",
    "name": "삼성전자",
    "sector": "IT/전자",
    "price": 70000,
    "historical_returns": [0.02, -0.01, 0.03, ...],
    "trading_volume": 15000000,
    "market_cap": 420000000000000,
    "debt_to_equity": 0.35,
    "current_ratio": 2.1,
    "credit_rating": "AA"
  }
]
```

### 필드 설명
- `ticker`: 종목 코드
- `name`: 종목명
- `sector`: 업종
- `price`: 현재가 (원)
- `historical_returns`: 과거 수익률 배열
- `trading_volume`: 일평균 거래량 (주)
- `market_cap`: 시가총액 (원)
- `debt_to_equity`: 부채비율
- `current_ratio`: 유동비율
- `credit_rating`: 신용등급 (AAA, AA, A, BBB, BB, B, CCC 등)

## 최적화 전략

### 1. 샤프 비율 최대화
전통적인 포트폴리오 이론에 기반한 최적화:
- 위험(변동성) 대비 수익률 극대화
- 효율적 투자선 상의 최적점 탐색

```python
portfolio = optimizer.optimize_max_sharpe()
```

### 2. 위험 인식 최적화
다중 위험 요소를 종합적으로 고려:
- 시장 위험: 변동성, VaR, 최대 낙폭
- 신용 위험: 부채비율, 신용등급, 집중도
- 유동성 위험: 거래량, 시가총액, 청산 용이성

```python
portfolio = optimizer.optimize_risk_aware(
    min_expected_return=0.05,      # 최소 5% 수익률
    max_volatility=0.15,           # 최대 15% 변동성
    min_credit_score=40.0,         # 최소 신용 점수
    min_liquidity_score=40.0       # 최소 유동성 점수
)
```

## 위험 관리 권장사항

### 시장 위험 관리
1. **분산투자**: 다양한 업종에 투자하여 개별 위험 감소
2. **VaR 모니터링**: 정기적으로 VaR 측정 및 한도 설정
3. **스트레스 테스트**: 극단적 시장 상황 시뮬레이션

### 신용 위험 관리
1. **신용등급 확인**: 투자 전 기업 신용등급 확인
2. **재무비율 분석**: 부채비율, 유동비율 등 재무 건전성 평가
3. **집중도 제한**: 단일 종목/섹터 비중 제한 (예: 40% 이하)

### 유동성 위험 관리
1. **거래량 확인**: 일평균 거래량이 충분한 종목 선택
2. **시가총액 고려**: 대형주/중형주 중심 포트폴리오 구성
3. **청산 계획**: 비상시 청산 소요 시간 사전 파악

## 주의사항

1. **과거 데이터 기반**: 과거 수익률이 미래 수익률을 보장하지 않습니다.
2. **시뮬레이션 한계**: 실제 시장에서는 슬리피지, 거래비용 등이 발생합니다.
3. **데이터 품질**: 정확한 분석을 위해서는 최신의 신뢰할 수 있는 데이터가 필요합니다.
4. **전문가 상담**: 실제 투자 결정 전 금융 전문가와 상담하시기 바랍니다.

## 확장 가능성

이 시스템은 다음과 같이 확장할 수 있습니다:

1. **실시간 데이터 연동**: API를 통한 실시간 시세 및 재무 데이터 수집
2. **백테스팅**: 과거 데이터로 전략 성과 검증
3. **리스크 패리티**: 위험 기여도 균등 배분 전략
4. **블랙-리터만 모델**: 시장 전망을 반영한 최적화
5. **머신러닝**: 수익률 예측 모델 통합

## 라이선스

이 프로젝트는 교육 및 연구 목적으로 제공됩니다.

## 기여

버그 리포트, 기능 제안, 코드 기여를 환영합니다.

## 면책 조항

이 소프트웨어는 교육 및 연구 목적으로만 제공됩니다. 실제 투자에 사용하여 발생하는 손실에 대해 개발자는 책임지지 않습니다. 투자 결정은 본인의 판단과 책임하에 이루어져야 합니다.
