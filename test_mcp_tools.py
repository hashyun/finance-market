#!/usr/bin/env python3
"""
MCP 도구 테스트 스크립트
각 도구의 기능을 테스트합니다
"""
import json
import numpy as np
from src.models.stock import Stock, Portfolio
from src.risk.market_risk import MarketRiskAnalyzer
from src.risk.credit_risk import CreditRiskAnalyzer
from src.risk.liquidity_risk import LiquidityRiskAnalyzer
from src.portfolio.optimizer import PortfolioOptimizer
from src.data_sources import BondClient

print("=" * 80)
print("MCP 도구 테스트")
print("=" * 80)

# 1. 포트폴리오 리스크 분석 테스트
print("\n[1] 포트폴리오 리스크 분석 테스트")
print("-" * 80)

# 샘플 주식 데이터
stocks = [
    Stock(
        ticker="005930",
        name="삼성전자",
        sector="IT/전자",
        price=70000,
        historical_returns=np.random.normal(0.001, 0.02, 252),
        trading_volume=15000000,
        market_cap=420000000000000,
        debt_to_equity=0.35,
        current_ratio=2.1,
        credit_rating="AA"
    ),
    Stock(
        ticker="000660",
        name="SK하이닉스",
        sector="IT/전자",
        price=135000,
        historical_returns=np.random.normal(0.0015, 0.025, 252),
        trading_volume=3000000,
        market_cap=98000000000000,
        debt_to_equity=0.45,
        current_ratio=1.8,
        credit_rating="A"
    ),
    Stock(
        ticker="035420",
        name="NAVER",
        sector="인터넷",
        price=230000,
        historical_returns=np.random.normal(0.0008, 0.022, 252),
        trading_volume=800000,
        market_cap=75000000000000,
        debt_to_equity=0.15,
        current_ratio=3.5,
        credit_rating="AA"
    ),
]

weights = [0.4, 0.3, 0.3]
portfolio = Portfolio(stocks, weights)

# 리스크 분석
var_95 = MarketRiskAnalyzer.value_at_risk(portfolio, 0.95)
cvar_95 = MarketRiskAnalyzer.conditional_var(portfolio, 0.95)
max_dd = MarketRiskAnalyzer.maximum_drawdown(portfolio)
div_ratio = MarketRiskAnalyzer.diversification_ratio(portfolio)

credit_score = CreditRiskAnalyzer.portfolio_credit_score(portfolio)
concentration = CreditRiskAnalyzer.concentration_risk(portfolio)
sector_exp = CreditRiskAnalyzer.sector_exposure(portfolio)

liquidity_score = LiquidityRiskAnalyzer.portfolio_liquidity_score(portfolio)

result = {
    "포트폴리오 수익률": f"{portfolio.expected_return():.2%}",
    "포트폴리오 변동성": f"{portfolio.volatility():.2%}",
    "샤프 비율": f"{portfolio.sharpe_ratio(0.035):.2f}",
    "시장 리스크": {
        "VaR (95%)": f"{var_95:.2%}",
        "CVaR (95%)": f"{cvar_95:.2%}",
        "최대낙폭": f"{max_dd:.2%}",
        "분산투자비율": f"{div_ratio:.2f}"
    },
    "신용 리스크": {
        "신용점수": f"{credit_score:.1f}/100",
        "집중도 (HHI)": f"{concentration:.3f}",
        "섹터별 노출도": {k: f"{v:.1%}" for k, v in sector_exp.items()}
    },
    "유동성 리스크": {
        "유동성점수": f"{liquidity_score:.1f}/100"
    }
}

print(json.dumps(result, ensure_ascii=False, indent=2))
print("✓ 포트폴리오 리스크 분석 성공")

# 2. 포트폴리오 최적화 테스트
print("\n[2] 포트폴리오 최적화 테스트")
print("-" * 80)

optimizer = PortfolioOptimizer(stocks, risk_free_rate=0.035)

# 샤프 비율 최대화
portfolio_sharpe = optimizer.optimize_max_sharpe()
analysis_sharpe = optimizer.analyze_portfolio(portfolio_sharpe)

result_sharpe = {
    "최적화 방법": "max_sharpe",
    "포트폴리오 구성": {
        stock.ticker: f"{weight:.1%}"
        for stock, weight in zip(portfolio_sharpe.stocks, portfolio_sharpe.weights)
    },
    "성과 지표": {
        "기대수익률": f"{analysis_sharpe['expected_return']:.2%}",
        "변동성": f"{analysis_sharpe['volatility']:.2%}",
        "샤프비율": f"{analysis_sharpe['sharpe_ratio']:.2f}",
        "신용점수": f"{analysis_sharpe['credit_score']:.1f}/100",
        "유동성점수": f"{analysis_sharpe['liquidity_score']:.1f}/100"
    }
}

print(json.dumps(result_sharpe, ensure_ascii=False, indent=2))
print("✓ 포트폴리오 최적화 성공")

# 3. 국채 수익률 조회 테스트
print("\n[3] 국채 수익률 조회 테스트")
print("-" * 80)

try:
    bond_client = BondClient()
    yield_curve = bond_client.get_yield_curve()

    if yield_curve:
        print("현재 국채 수익률 곡선:")
        print(json.dumps(yield_curve, ensure_ascii=False, indent=2))
        print("✓ 국채 수익률 조회 성공")
    else:
        print("⚠ 국채 수익률 데이터를 조회할 수 없습니다 (네트워크 오류 또는 영업일 아님)")

    # 수익률 곡선 형태 분석
    shape_analysis = bond_client.analyze_yield_curve_shape()
    if shape_analysis:
        print("\n수익률 곡선 형태 분석:")
        print(json.dumps(shape_analysis, ensure_ascii=False, indent=2, default=str))
        print("✓ 수익률 곡선 분석 성공")

except Exception as e:
    print(f"⚠ 국채 수익률 조회 중 오류: {e}")

# 4. 외부 API 테스트 (선택사항)
print("\n[4] 외부 API 연동 테스트")
print("-" * 80)

try:
    from src.data_sources import FREDClient
    fred = FREDClient()
    print("✓ FRED API 연결 성공")
except Exception as e:
    print(f"⚠ FRED API: {e}")

try:
    from src.data_sources import ECOSClient
    ecos = ECOSClient()
    print("✓ ECOS API 연결 성공")
except Exception as e:
    print(f"⚠ ECOS API: {e}")

try:
    from src.data_sources import DARTClient
    dart = DARTClient()
    print("✓ DART API 연결 성공")
except Exception as e:
    print(f"⚠ DART API: {e}")

print("\n" + "=" * 80)
print("MCP 도구 테스트 완료")
print("=" * 80)
print("\n다음 단계:")
print("1. .env 파일에 API 키를 설정하세요 (선택사항)")
print("2. Claude Desktop 설정 파일을 편집하세요 (MCP_SETUP.md 참조)")
print("3. Claude Desktop을 재시작하세요")
print("4. Claude Desktop에서 finance-market 도구를 사용하세요")
