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

---

## 알고리즘 트레이딩 (한국 시장 특화)

### 한국 시장 특화 기능

#### 1. 투자자별 수급 분석
- **외국인 매매**: 외국인 순매수/매도 추적
- **기관 매매**: 기관 투자자 동향 분석
- **개인 매매**: 개인 투자자 흐름 파악
- **프로그램 매매**: 알고리즘 매매 감지
- **투자자 컨센서스**: 외국인+기관 일치도 분석

#### 2. 한국 시장 지표
- **공매도 분석**: 공매도 비율 및 숏 스퀴즈 가능성
- **신용잔고**: 신용거래 동향
- **거래대금 회전율**: 유동성 지표
- **코스피/코스닥 구분**: 시장별 특성 반영

#### 3. 트레이딩 전략

##### 외국인 수급 추종 전략
외국인과 기관의 매수세가 강한 종목을 선택합니다.

```python
from src.strategies.foreign_follow import ForeignFollowStrategy

strategy = ForeignFollowStrategy(
    buy_threshold=30.0,
    sell_threshold=-30.0
)
```

**특징:**
- 외국인 + 기관 컨센서스 분석
- 프로그램 매매 신호 통합
- 대형 우량주에 효과적

##### 모멘텀 전략
가격 상승 추세가 강한 종목을 매수합니다.

```python
from src.strategies.momentum import MomentumStrategy

strategy = MomentumStrategy(
    rsi_buy_max=70,
    rsi_sell_min=30
)
```

**특징:**
- 이동평균 정배열 확인
- RSI, MACD 종합 판단
- 중소형 성장주에 효과적

##### 평균회귀 전략
과매도 구간에서 매수, 과매수 구간에서 매도합니다.

```python
from src.strategies.mean_reversion import MeanReversionStrategy

strategy = MeanReversionStrategy(
    bb_lower_threshold=20,
    bb_upper_threshold=80
)
```

**특징:**
- 볼린저 밴드 기반
- 스토캐스틱, RSI 활용
- 박스권 종목에 효과적

##### 멀티 전략 (복합 전략)
여러 전략을 조합하여 사용합니다.

```python
from src.strategies.multi_strategy import MultiStrategy

multi_strategy = MultiStrategy(
    strategies=[foreign_strategy, momentum_strategy, reversion_strategy],
    weights=[0.5, 0.3, 0.2]
)
```

### 백테스팅

전략의 과거 성과를 검증합니다.

```python
from src.backtest.backtester import Backtester

backtester = Backtester(
    initial_capital=100_000_000,  # 1억원
    commission_rate=0.00015,      # 수수료 0.015%
    tax_rate=0.0023,              # 거래세 0.23%
    max_position_size=0.3         # 최대 포지션 30%
)

result = backtester.run(
    stocks=stocks,
    strategy=strategy,
    rebalance_period=5  # 5일마다 리밸런싱
)

print(f"수익률: {result.total_return_pct:.2f}%")
print(f"승률: {result.win_rate:.2f}%")
print(f"샤프 비율: {result.sharpe_ratio:.2f}")
print(f"최대 낙폭: {result.max_drawdown:.2f}%")
```

### 알고리즘 트레이딩 예제 실행

```bash
python examples/algo_trading_example.py
```

이 예제는 다음을 수행합니다:
1. 한국 시장 샘플 데이터 생성 (외국인/기관 매매 포함)
2. 개별 종목 수급 분석
3. 여러 전략의 매매 신호 생성
4. 백테스팅을 통한 전략 성과 비교
5. 투자자 유형별 전략 추천

### 실전 활용 팁

#### 강한 매수 신호
- 외국인 + 기관 동시 순매수
- 이동평균 정배열 + RSI 50 이상
- 프로그램 매수 급증

#### 저점 매수 기회
- 외국인 지속 매수 + 가격 하락
- RSI 과매도 (30 이하) + 볼린저 밴드 하단
- 공매도 비율 높고 외국인 매수

#### 고점 매도 신호
- 외국인 + 기관 동시 순매도
- RSI 과매수 (70 이상) + 볼린저 밴드 상단
- 프로그램 매도 급증

#### 숏 스퀴즈 포착
- 공매도 비율 10% 이상
- 외국인/기관 순매수 전환
- 급격한 거래량 증가

## 프로젝트 구조 (전체)

```
finance-market/
├── src/
│   ├── models/
│   │   ├── stock.py                  # 기본 Stock, Portfolio 클래스
│   │   └── korean_stock.py           # 한국 시장 특화 데이터 모델
│   ├── risk/
│   │   ├── market_risk.py            # 시장 위험 분석
│   │   ├── credit_risk.py            # 신용 위험 분석
│   │   └── liquidity_risk.py         # 유동성 위험 분석
│   ├── portfolio/
│   │   └── optimizer.py              # 포트폴리오 최적화
│   ├── analysis/
│   │   ├── investor_flow.py          # 투자자 수급 분석
│   │   └── market_indicators.py      # 기술적 지표
│   ├── strategies/
│   │   ├── base_strategy.py          # 전략 베이스 클래스
│   │   ├── foreign_follow.py         # 외국인 수급 추종
│   │   ├── momentum.py               # 모멘텀 전략
│   │   ├── mean_reversion.py         # 평균회귀 전략
│   │   └── multi_strategy.py         # 멀티 전략
│   ├── backtest/
│   │   └── backtester.py             # 백테스팅 엔진
│   └── utils/
│       ├── data_loader.py            # 데이터 로딩
│       └── data_generator.py         # 샘플 데이터 생성
├── examples/
│   ├── portfolio_example.py          # 포트폴리오 최적화 예제
│   └── algo_trading_example.py       # 알고리즘 트레이딩 예제
├── data/
│   └── sample_stocks.json            # 샘플 데이터
├── requirements.txt
└── README.md
```

## 한국 시장 데이터 형식

한국 시장 특화 데이터는 다음 정보를 포함합니다:

```python
TradingData(
    date="2024-01-01",
    open=70000,
    high=71000,
    low=69500,
    close=70500,
    volume=15000000,
    # 한국 시장 특화
    foreign_buy=2000000,       # 외국인 매수량
    foreign_sell=1500000,      # 외국인 매도량
    institution_buy=1000000,   # 기관 매수량
    institution_sell=800000,   # 기관 매도량
    individual_buy=5000000,    # 개인 매수량
    individual_sell=5700000,   # 개인 매도량
    program_buy=3000000,       # 프로그램 매수량
    program_sell=2800000,      # 프로그램 매도량
    short_sell_volume=500000,  # 공매도 거래량
    short_balance=2000000,     # 공매도 잔고
    credit_balance=150.5       # 신용잔고 (억원)
)
```

## 참고 자료

### 한국 시장 특성
- **외국인 투자자**: 대형주 선호, 장기 투자 성향
- **기관 투자자**: 중기 트렌드 추종, 테마 투자
- **개인 투자자**: 단기 매매, 역발상 투자
- **프로그램 매매**: 차익거래, 비차익거래 구분

### 투자 유의사항
1. 과거 데이터는 미래를 보장하지 않습니다
2. 백테스팅 결과와 실전 결과는 다를 수 있습니다
3. 슬리피지, 유동성 리스크 등을 고려해야 합니다
4. 적절한 리스크 관리가 필수적입니다


---

## 실시간 트레이딩 시스템

### 1. 실시간 데이터 연동

#### API 클라이언트

모든 증권사 API에 대응할 수 있는 추상 인터페이스를 제공합니다.

```python
from src.api.base_client import BaseAPIClient

class YourAPIClient(BaseAPIClient):
    """실제 증권사 API 구현"""
    
    def connect(self) -> bool:
        # API 연결 로직
        pass
    
    def get_market_data(self, ticker: str):
        # 실시간 시세 조회
        pass
```

#### Mock API (테스트용)

실제 API 없이도 시스템을 테스트할 수 있습니다.

```python
from src.api.mock_client import MockAPIClient

# Mock API 초기화
api_client = MockAPIClient(initial_balance=100_000_000)
api_client.connect()

# 실시간 시세 조회
market_data = api_client.get_market_data('005930')
print(f"삼성전자 현재가: {market_data.price:,.0f}원")
print(f"외국인 순매수: {market_data.foreign_net:,}주")

# 주문 실행
from src.api.base_client import OrderRequest

order = OrderRequest(
    ticker='005930',
    order_type='BUY',
    quantity=10,
    order_method='MARKET'
)

response = api_client.place_order(order)
print(f"주문 결과: {response.status}")
```

### 2. 자동 포트폴리오 리밸런싱

#### 리밸런서 설정

```python
from src.rebalance.rebalancer import PortfolioRebalancer

rebalancer = PortfolioRebalancer(
    api_client=api_client,
    strategy=your_strategy,
    target_tickers=['005930', '000660', '035420'],
    rebalance_threshold=0.05,      # 5% 이상 벗어나면 리밸런싱
    min_trade_amount=100_000,      # 최소 거래 금액
    max_position_size=0.4          # 최대 포지션 40%
)
```

#### 리밸런싱 미리보기

```python
# 실제 주문 없이 리밸런싱 계획 확인
preview = rebalancer.get_rebalancing_preview()

print(f"리밸런싱 필요: {preview['needs_rebalancing']}")

for ticker, info in preview['deviations'].items():
    print(f"{ticker}: {info['current']:.1%} → {info['target']:.1%}")
    print(f"  액션: {info['action']}")
```

#### 자동 리밸런싱 실행

```python
# 리밸런싱 체크 및 실행
result = rebalancer.run_rebalancing_check()

if result:
    print(f"리밸런싱 완료: {result.message}")
    print(f"실행된 주문: {len(result.orders_executed)}개")
    
    for order in result.orders_executed:
        print(f"  {order['order_type']}: {order['ticker']} "
              f"{order['quantity']}주 @ {order['price']:,.0f}원")
```

#### 리밸런싱 트리거 조건

1. **비중 이탈**: 목표 비중에서 임계값 이상 벗어남
2. **시장 조건 변화**: 전략 점수 변화
3. **수동 트리거**: 사용자가 직접 실행

### 3. 실시간 알림 시스템

#### 알림 설정

```python
from src.notification.notifier import Notifier, NotificationLevel
from src.notification.channels import ConsoleChannel, FileChannel

# 알림 시스템 초기화
notifier = Notifier()

# 채널 추가
notifier.add_channel(ConsoleChannel(colored=True))
notifier.add_channel(FileChannel(log_file="logs/trading.log"))
```

#### 알림 전송

```python
# 정보 알림
notifier.info("시스템 시작", "트레이딩 시스템이 시작되었습니다.")

# 경고 알림
notifier.warning("리밸런싱 필요", "포트폴리오 비중이 목표에서 벗어났습니다.")

# 중요 알림
notifier.alert("매수 신호", "삼성전자 매수 신호 발생", {'ticker': '005930', 'price': 70000})

# 오류 알림
notifier.error("주문 실패", "잔고 부족으로 주문이 실패했습니다.")
```

#### 알림 채널

##### 콘솔 출력
```python
from src.notification.channels import ConsoleChannel

# 컬러 출력 지원
console_channel = ConsoleChannel(colored=True)
notifier.add_channel(console_channel)
```

##### 파일 로깅
```python
from src.notification.channels import FileChannel

# 파일에 로그 저장
file_channel = FileChannel(log_file="logs/trading.log")
notifier.add_channel(file_channel)
```

##### 이메일 (확장 가능)
```python
from src.notification.channels import EmailChannel

# 이메일 알림 (SMTP 설정 필요)
email_channel = EmailChannel(
    smtp_server="smtp.gmail.com",
    recipient="your@email.com"
)
notifier.add_channel(email_channel)
```

##### Slack (확장 가능)
```python
from src.notification.channels import SlackChannel

# Slack 웹훅
slack_channel = SlackChannel(webhook_url="your-webhook-url")
notifier.add_channel(slack_channel)
```

#### 알림 히스토리

```python
# 전체 알림 조회
all_notifications = notifier.get_history(limit=100)

# 특정 레벨만 조회
errors = notifier.get_history(level=NotificationLevel.ERROR, limit=50)
alerts = notifier.get_history(level=NotificationLevel.ALERT, limit=50)
```

### 4. 통합 실시간 트레이딩 예제

모든 기능을 통합한 실시간 트레이딩 시스템:

```bash
python examples/realtime_trading_example.py
```

#### 시스템 흐름

1. **API 연결**: Mock API 또는 실제 API 연결
2. **알림 시스템 초기화**: 여러 채널 설정
3. **전략 설정**: 외국인 수급 + 모멘텀 전략
4. **대상 종목 설정**: 리밸런싱 대상 종목 지정
5. **초기 포트폴리오 구성**: 목표 비중에 맞춰 매수
6. **실시간 모니터링**: 
   - 실시간 시세 조회
   - 리밸런싱 필요 여부 확인
   - 자동 리밸런싱 실행
   - 알림 전송
7. **최종 결과 출력**: 성과 분석

#### 실행 예제

```python
from src.api.mock_client import MockAPIClient
from src.strategies.multi_strategy import MultiStrategy
from src.rebalance.rebalancer import PortfolioRebalancer
from src.notification.notifier import Notifier

# 1. API 초기화
api_client = MockAPIClient(initial_balance=100_000_000)
api_client.connect()

# 2. 알림 설정
notifier = Notifier()
notifier.add_channel(ConsoleChannel(colored=True))

# 3. 전략 설정
strategy = MultiStrategy([foreign_strategy, momentum_strategy], [0.6, 0.4])

# 4. 리밸런서 설정
rebalancer = PortfolioRebalancer(
    api_client=api_client,
    strategy=strategy,
    target_tickers=['005930', '000660', '035420'],
    rebalance_threshold=0.05
)

# 5. 실시간 모니터링 루프
while True:
    # 실시간 시세 조회
    market_data = api_client.get_market_data_batch(target_tickers)
    
    # 리밸런싱 체크
    result = rebalancer.run_rebalancing_check()
    
    if result and result.success:
        notifier.alert("리밸런싱 완료", result.message)
    
    # 계좌 상태 확인
    account = api_client.get_account_balance()
    
    time.sleep(check_interval)
```

## 실전 활용 시나리오

### 시나리오 1: 외국인 매수 포착 자동 매매

```python
# 외국인 순매수 급증 감지
market_data = api_client.get_market_data('005930')

if market_data.foreign_net > 1_000_000:  # 100만주 이상 순매수
    notifier.alert("외국인 매수 급증", f"삼성전자 외국인 순매수: {market_data.foreign_net:,}주")
    
    # 자동 매수
    order = OrderRequest(ticker='005930', order_type='BUY', quantity=10)
    response = api_client.place_order(order)
```

### 시나리오 2: 손절/익절 자동화

```python
holdings = api_client.get_holdings()

for ticker, holding in holdings.items():
    # 손절: -5% 이하
    if holding['profit_loss_pct'] <= -5.0:
        notifier.warning("손절 실행", f"{ticker} 손실률 {holding['profit_loss_pct']:.2f}%")
        # 전량 매도
        
    # 익절: +10% 이상
    elif holding['profit_loss_pct'] >= 10.0:
        notifier.info("익절 실행", f"{ticker} 수익률 {holding['profit_loss_pct']:.2f}%")
        # 일부 매도
```

### 시나리오 3: 일일 리밸런싱 스케줄링

```python
import schedule

def daily_rebalancing():
    """매일 장 시작 후 리밸런싱"""
    result = rebalancer.run_rebalancing_check()
    
    if result:
        notifier.alert("일일 리밸런싱", result.message)

# 매일 오전 9시 10분 실행
schedule.every().day.at("09:10").do(daily_rebalancing)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## 주의사항

### 실시간 데이터 연동
- API 호출 제한(Rate Limit)에 주의
- 네트워크 장애 대응 필요
- API 키 보안 관리 필수

### 자동 리밸런싱
- 과도한 리밸런싱은 수수료 증가
- 시장 충격 최소화를 위한 분할 매매 고려
- 장 마감 직전 리밸런싱 주의

### 알림 시스템
- 알림 스팸 방지 (중복 알림 필터링)
- 중요도에 따른 채널 분리
- 알림 히스토리 정기적 정리

## 확장 가능성

1. **실제 증권사 API 연동**: KIS API, eBest API 등
2. **고급 주문 전략**: 분할 매매, 조건부 주문
3. **머신러닝 통합**: 실시간 예측 모델
4. **대시보드**: 웹 기반 실시간 모니터링
5. **백업 시스템**: 이중화 및 장애 복구

---

## KRX API + 수동 매매 시스템

증권사 API를 제공하지 않는 경우, KRX API로 시장 데이터를 가져오고 포지션을 수동으로 관리하는 방식입니다.

### 시스템 구성

```
KRX API → 시장 데이터 (시세, 외국인/기관 매매 등)
포지션 파일 → 보유 종목 정보 (수동 관리)
어드바이저 → 리밸런싱 추천 (자동 분석)
증권사 앱/HTS → 실제 매매 (수동 실행)
```

### 1. KRX API 클라이언트

KRX 정보데이터시스템과 DART의 공식 API를 직접 사용하여 시세 및 투자자별 매매 동향을 조회합니다.

```python
from src.api.krx_client import KRXAPIClient

# KRX API 클라이언트 초기화
api_client = KRXAPIClient(
    position_file="data/my_positions.json",
    dart_api_key="your-dart-api-key"  # 선택사항
)
api_client.connect()

# 실시간 시세 조회
market_data = api_client.get_market_data('005930')  # 삼성전자

print(f"현재가: {market_data.price:,.0f}원")
print(f"외국인 순매수: {market_data.foreign_net:,}주")
print(f"기관 순매수: {market_data.institution_net:,}주")

# 여러 종목 일괄 조회
tickers = ['005930', '000660', '035420']
market_data_batch = api_client.get_market_data_batch(tickers)

# 투자자별 매매 동향 (기간 합산)
investor_flow = api_client.get_investor_flow('005930', days=20)
```

#### 데이터 소스

- **KRX 정보데이터시스템 (data.krx.co.kr)**: 공식 시장 데이터
  - 개별 종목 시세 (OHLCV)
  - 투자자별 매매 동향 (외국인/기관/개인)
- **DART (opendart.fss.or.kr)**: 기업 정보 (선택사항)
  - API 키 발급: https://opendart.fss.or.kr/
- **포지션 파일**: 사용자가 직접 관리하는 보유 종목 정보

#### KRX API 엔드포인트

본 시스템은 다음 KRX API를 직접 호출합니다:

1. **개별종목 시세** (`MDCSTAT01501`)
   - 종가, 시가, 고가, 저가, 거래량

2. **투자자별 매매동향** (`MDCSTAT02203`)
   - 외국인, 기관, 개인 순매수량

### 2. 포지션 파일 관리

#### 포지션 파일 형식 (data/my_positions.json)

```json
{
  "cash": 50000000,
  "holdings": {
    "005930": {
      "name": "삼성전자",
      "quantity": 100,
      "avg_price": 72000
    },
    "000660": {
      "name": "SK하이닉스",
      "quantity": 50,
      "avg_price": 135000
    },
    "035420": {
      "name": "NAVER",
      "quantity": 30,
      "avg_price": 230000
    }
  }
}
```

#### 포지션 파일 업데이트 도구

매매 후 포지션을 쉽게 업데이트할 수 있는 대화형 도구를 제공합니다.

```bash
python tools/update_positions.py
```

**기능:**
- 현금 잔고 업데이트
- 보유 종목 추가/수정/삭제
- 매매 기록 (자동 계산)
  - 매수: 평균단가 자동 재계산, 현금 차감
  - 매도: 수량 차감, 현금 증가

### 3. 리밸런싱 추천 시스템

#### 어드바이저 초기화

```python
from src.advisor.manual_trading_advisor import ManualTradingAdvisor
from src.strategies.multi_strategy import MultiStrategy

# 전략 설정
strategy = MultiStrategy([foreign_strategy, momentum_strategy], [0.6, 0.4])

# 어드바이저 초기화
advisor = ManualTradingAdvisor(
    api_client=api_client,
    strategy=strategy,
    target_tickers=['005930', '000660', '035420'],
    rebalance_threshold=0.05,  # 5% 이상 벗어나면 추천
    min_trade_amount=100_000,
    max_position_size=0.4
)
```

#### 포트폴리오 분석

```python
# 포트폴리오 상태 분석
analysis = advisor.get_portfolio_analysis()

print(f"총 자산: {analysis['total_value']:,.0f}원")
print(f"손익률: {analysis['profit_loss_pct']:.2f}%")
print(f"리밸런싱 필요: {analysis['needs_rebalancing']}")

# 현재 비중 vs 목표 비중
for ticker in target_tickers:
    current = analysis['current_weights'][ticker]
    target = analysis['target_weights'][ticker]
    deviation = analysis['deviations'][ticker]

    print(f"{ticker}: {current:.1%} → {target:.1%} (차이: {deviation:+.1%})")
```

#### 매매 추천 받기

```python
# 매매 추천 생성
recommendations = advisor.get_trading_recommendations()

for rec in recommendations:
    if rec.action == "BUY":
        print(f"📈 매수: {rec.ticker}")
        print(f"   수량: {rec.recommended_quantity:,}주")
        print(f"   예상가: {rec.estimated_price:,.0f}원")
        print(f"   예상금액: {rec.estimated_amount:,.0f}원")
        print(f"   이유: {rec.reason}")

    elif rec.action == "SELL":
        print(f"📉 매도: {rec.ticker}")
        print(f"   수량: {rec.recommended_quantity:,}주")
        print(f"   예상가: {rec.estimated_price:,.0f}원")
        print(f"   예상금액: {rec.estimated_amount:,.0f}원")
        print(f"   이유: {rec.reason}")
```

#### 매매 가이드 출력

```python
# 전체 분석 및 매매 가이드 출력
advisor.print_trading_guide()
```

출력 예시:
```
================================================================================
  포트폴리오 분석 및 매매 가이드
================================================================================

[계좌 현황]
  총 자산:          100,000,000원
  현금 잔고:         50,000,000원
  주식 평가액:       50,000,000원
  손익:              +2,000,000원 (+4.17%)

[포트폴리오 비중]
  종목        현재비중      목표비중          차이        상태
  ------------------------------------------------------------------------
  005930         30.0%        33.3%        +3.3%    🔴 매수필요
  000660         20.0%        33.3%       +13.3%    🔴 매수필요
  035420         50.0%        33.3%       -16.7%    🔵 매도필요

[매매 추천]
  리밸런싱 필요: 예 (임계값: 5.0%)

  📉 매도 추천:
    • 035420: 15주 @ 230,000원
      (예상 금액: 3,450,000원)
      이유: 목표 비중(33.3%)보다 16.7%p 높음

  📈 매수 추천:
    • 005930: 15주 @ 72,000원
      (예상 금액: 1,080,000원)
      이유: 목표 비중(33.3%)보다 3.3%p 낮음

    • 000660: 10주 @ 135,000원
      (예상 금액: 1,350,000원)
      이유: 목표 비중(33.3%)보다 13.3%p 낮음

  💡 실행 순서:
    1. 매도 주문을 먼저 실행하여 현금을 확보하세요
    2. 매도 체결 후 매수 주문을 실행하세요
    3. 주문 체결 후 포지션 파일을 업데이트하세요

  총 매도 예상액:        3,450,000원
  총 매수 예상액:        2,430,000원
  순 현금 변동:          1,020,000원
```

#### 추천 파일로 저장

```python
# JSON 파일로 저장
advisor.export_recommendations_to_file("data/trading_recommendations.json")
```

### 4. 실행 예제

#### 수동 매매 예제 실행

```bash
python examples/manual_trading_example.py
```

**시스템 흐름:**
1. 포지션 파일 로드
2. KRX API 연결
3. 현재 포트폴리오 상태 확인
4. 전략 기반 리밸런싱 분석
5. 매매 추천 생성 및 출력
6. 추천 파일로 저장

### 5. 실전 운영 가이드

#### 일일 루틴

**1. 장 시작 전 (9:00 이전)**
```bash
# 포트폴리오 분석 실행
python examples/manual_trading_example.py
```

- 어제 매매 반영 확인
- 포지션 파일 최신화
- 오늘의 매매 전략 확인

**2. 장 중 (9:00 ~ 15:30)**

- 추천된 매매를 증권사 앱/HTS에서 실행
- 시장 상황 모니터링
- 급변 시 재분석 실행

**3. 장 마감 후 (15:30 이후)**

```bash
# 포지션 업데이트
python tools/update_positions.py
```

- 오늘 체결된 주문 반영
- 보유 수량, 평균단가 업데이트
- 현금 잔고 정리

#### 매매 실행 팁

**매수 시:**
1. 추천 가격을 참고하되, HTS에서 최신 시세 확인
2. 지정가 주문으로 슬리피지 최소화
3. 분할 매수 고려 (대량 매수 시)

**매도 시:**
1. 매도부터 실행하여 현금 확보
2. 급등/급락 시 시장가 대신 지정가 활용
3. 시장 충격 최소화 (대량 매도 시)

**포지션 업데이트:**
1. 체결가 정확히 입력
2. 평균단가는 도구가 자동 계산
3. 수수료/세금은 도구에서 자동 반영

### 6. 장점과 한계

#### 장점

✅ **증권사 API 불필요**
- API를 제공하지 않는 증권사도 사용 가능
- API 연동 비용/제한 없음

✅ **실시간 시장 데이터**
- KRX 공식 데이터 활용
- 외국인/기관 매매 동향 확인
- 무료로 이용 가능

✅ **전략 기반 추천**
- 알고리즘 기반 리밸런싱 추천
- 다양한 전략 조합 가능
- 위험 관리 자동화

✅ **완전한 통제**
- 매매 시점 직접 결정
- 가격 협상력 유지
- 시장 상황 판단 반영

#### 한계

⚠️ **수동 실행 필요**
- 자동 매매 불가
- 사용자가 직접 주문 실행
- 신속한 대응 어려움

⚠️ **포지션 관리**
- 매매 후 수동 업데이트 필요
- 실수 가능성 존재
- 동기화 주의 필요

⚠️ **데이터 지연**
- 실시간이 아닌 준실시간
- API 호출 제한 있음
- 네트워크 의존성

### 7. 문제 해결

#### API 오류

**시세 조회 실패:**
```python
# 재시도 로직
for i in range(3):
    market_data = api_client.get_market_data(ticker)
    if market_data:
        break
    time.sleep(1)
```

**네트워크 오류:**
- 인터넷 연결 확인
- 방화벽 설정 확인
- 타임아웃 설정 조정

#### 포지션 파일 오류

**파일 형식 오류:**
```bash
# JSON 유효성 검사
python -m json.tool data/my_positions.json
```

**백업 및 복구:**
```bash
# 백업
cp data/my_positions.json data/my_positions.backup.json

# 복구
cp data/my_positions.backup.json data/my_positions.json
```

#### 매매 추천 검증

**추천 재확인:**
1. 시장 상황 급변 시 재분석
2. 이상한 추천은 무시
3. 소액으로 먼저 테스트

**리스크 관리:**
- 한 번에 큰 금액 투자 지양
- 분할 매매 활용
- 손절선 설정

### 8. 실제 사용 예시

#### Case 1: 외국인 매수 종목 포착

```bash
# 1. 시스템 실행
python examples/manual_trading_example.py

# 출력:
# [실시간 시세]
#   종목        현재가    외국인순매수      기관순매수
#   005930     72,000원      +1,500,000주      +500,000주
#   000660    135,000원        +800,000주      +200,000주
#
# [매매 추천]
#   📈 매수: 005930 (외국인+기관 동시 순매수)

# 2. 증권사 앱에서 삼성전자 매수

# 3. 포지션 업데이트
python tools/update_positions.py
# 메뉴에서 4번 선택 → 매수 기록
```

#### Case 2: 리밸런싱

```bash
# 1. 주간 리밸런싱 실행 (매주 월요일)
python examples/manual_trading_example.py

# 출력:
# [매매 추천]
#   📉 매도: 035420 15주 (비중 초과)
#   📈 매수: 000660 10주 (비중 부족)

# 2. HTS에서 순서대로 실행
#    - NAVER 15주 매도
#    - SK하이닉스 10주 매수

# 3. 포지션 업데이트
python tools/update_positions.py
```

#### Case 3: 신규 종목 추가

```bash
# 1. 포지션 파일 직접 편집
# data/my_positions.json에 새 종목 추가

# 2. 시스템 재실행하여 리밸런싱 확인
python examples/manual_trading_example.py

# 3. 추천에 따라 매매 실행
```

### 9. 고급 활용

#### 전략 커스터마이징

```python
# 나만의 전략 비중 조정
strategy = MultiStrategy(
    strategies=[
        ForeignFollowStrategy(),  # 외국인 수급
        MomentumStrategy(),       # 모멘텀
        MeanReversionStrategy()   # 평균회귀
    ],
    weights=[0.5, 0.3, 0.2]  # 비중 조정
)
```

#### 자동화 스크립트

```bash
#!/bin/bash
# daily_check.sh - 매일 자동 실행

# 1. 포트폴리오 분석
python examples/manual_trading_example.py > daily_report.txt

# 2. 이메일로 리포트 전송
mail -s "오늘의 매매 추천" your@email.com < daily_report.txt

# Cron 설정: 매일 오전 8시 50분 실행
# 50 8 * * 1-5 /path/to/daily_check.sh
```

#### 다중 포트폴리오 관리

```python
# 포트폴리오별 관리
portfolios = {
    'aggressive': 'data/positions_aggressive.json',
    'moderate': 'data/positions_moderate.json',
    'conservative': 'data/positions_conservative.json'
}

for name, file in portfolios.items():
    api_client = KRXAPIClient(position_file=file)
    api_client.connect()
    # 분석 및 추천...
```

### 10. 참고 자료

#### API 및 데이터 출처
- **KRX 정보데이터시스템**: http://data.krx.co.kr
  - 개별 종목 시세, 투자자별 매매 동향
  - 별도 인증 불필요 (공개 API)
- **DART (전자공시시스템)**: https://opendart.fss.or.kr
  - 기업 재무정보, 공시정보
  - API 키 발급 필요 (무료)

#### 증권사별 매매 방법
- 각 증권사 HTS/MTS 매뉴얼 참고
- 지정가/시장가 주문 방법
- 조건부 주문 활용

#### 투자 유의사항
- 이 시스템은 투자 조언이 아닌 정보 제공 목적입니다
- 투자 결정과 책임은 본인에게 있습니다
- 충분한 테스트 후 소액으로 시작하세요
- 시장 상황을 항상 주시하세요

