"""
한국 주식 포트폴리오 최적화 예제
Market Risk, Credit Risk, Liquidity Risk를 고려한 스마트 포트폴리오 구성
"""
import sys
import os

# 상위 디렉토리의 src 모듈을 import하기 위한 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.data_loader import DataLoader
from src.models.stock import Portfolio
from src.portfolio.optimizer import PortfolioOptimizer
from src.risk.market_risk import MarketRiskAnalyzer
from src.risk.credit_risk import CreditRiskAnalyzer
from src.risk.liquidity_risk import LiquidityRiskAnalyzer


def print_section(title):
    """섹션 제목 출력"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_portfolio_weights(portfolio):
    """포트폴리오 비중 출력"""
    print("\n[포트폴리오 구성]")
    weights_dict = portfolio.get_weights_dict()
    for stock in portfolio.stocks:
        weight = weights_dict[stock.ticker]
        if weight > 0.001:  # 0.1% 이상만 출력
            print(f"  {stock.name:15s} ({stock.ticker}): {weight:6.2%}")


def print_analysis(analysis):
    """포트폴리오 분석 결과 출력"""
    print("\n[기본 성과 지표]")
    print(f"  기대 수익률:        {analysis['expected_return']:6.2%}")
    print(f"  변동성 (표준편차):   {analysis['volatility']:6.2%}")
    print(f"  샤프 비율:          {analysis['sharpe_ratio']:6.2f}")

    print("\n[시장 위험 지표]")
    print(f"  VaR (95%):         {analysis['var_95']:6.2%}")
    print(f"  CVaR (95%):        {analysis['cvar_95']:6.2%}")
    print(f"  최대 낙폭:          {analysis['max_drawdown']:6.2%}")
    print(f"  분산투자 비율:      {analysis['diversification_ratio']:6.2f}")

    print("\n[신용 위험 지표]")
    print(f"  신용 점수:          {analysis['credit_score']:6.1f}/100")
    print(f"  집중 위험 (HHI):    {analysis['concentration_risk']:6.3f}")
    print(f"  평균 부채비율:      {analysis['weights']['105560']:6.2f}" if '105560' in analysis['weights'] else "")

    print("\n[유동성 위험 지표]")
    print(f"  유동성 점수:        {analysis['liquidity_score']:6.1f}/100")
    print(f"  최대 청산 소요:     {analysis['max_liquidation_days']:6.2f}일")

    print("\n[종합 위험 지표]")
    print(f"  종합 위험 점수:     {analysis['composite_risk_score']:6.1f}/100 (낮을수록 좋음)")
    print(f"  위험조정수익률:     {analysis['risk_adjusted_return']:6.3f}")

    print("\n[섹터별 노출도]")
    for sector, weight in analysis['sector_exposure'].items():
        if weight > 0.001:
            print(f"  {sector:15s}: {weight:6.2%}")


def main():
    print_section("한국 주식 포트폴리오 위험 관리 시스템")

    # 1. 데이터 로드
    print("\n[1단계] 주식 데이터 로딩...")
    data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_stocks.json')
    stocks = DataLoader.load_from_json(data_file)
    print(f"  총 {len(stocks)}개 종목 로드 완료")
    for stock in stocks:
        print(f"    - {stock.name} ({stock.ticker}), {stock.sector}")

    # 2. 포트폴리오 최적화 엔진 생성
    print_section("포트폴리오 최적화")
    print("\n[2단계] 최적화 엔진 초기화...")
    print("  위험 가중치:")
    print("    - 시장 위험:   40%")
    print("    - 신용 위험:   30%")
    print("    - 유동성 위험: 30%")

    optimizer = PortfolioOptimizer(
        stocks=stocks,
        risk_free_rate=0.03,
        market_risk_weight=0.4,
        credit_risk_weight=0.3,
        liquidity_risk_weight=0.3
    )

    # 3. 전통적 최적화 (샤프 비율 최대화)
    print_section("전략 1: 샤프 비율 최대화")
    print("\n[3단계] 전통적 포트폴리오 최적화 (샤프 비율 최대화)...")
    traditional_portfolio = optimizer.optimize_max_sharpe()
    print_portfolio_weights(traditional_portfolio)

    print("\n[분석 결과]")
    traditional_analysis = optimizer.analyze_portfolio(traditional_portfolio)
    print_analysis(traditional_analysis)

    # 4. 위험 인식 최적화
    print_section("전략 2: 위험 인식 포트폴리오 (통합 위험 관리)")
    print("\n[4단계] 위험 인식 포트폴리오 최적화...")
    print("  제약 조건:")
    print("    - 최소 신용 점수:    40점")
    print("    - 최소 유동성 점수:  40점")
    print("    - 최대 종목 비중:    40%")

    risk_aware_portfolio = optimizer.optimize_risk_aware(
        min_credit_score=40.0,
        min_liquidity_score=40.0
    )
    print_portfolio_weights(risk_aware_portfolio)

    print("\n[분석 결과]")
    risk_aware_analysis = optimizer.analyze_portfolio(risk_aware_portfolio)
    print_analysis(risk_aware_analysis)

    # 5. 두 전략 비교
    print_section("전략 비교 분석")
    print("\n" + "-" * 70)
    print(f"{'지표':<25} {'샤프최대화':>15} {'위험인식':>15}")
    print("-" * 70)
    print(f"{'기대 수익률':<25} {traditional_analysis['expected_return']:>14.2%} {risk_aware_analysis['expected_return']:>14.2%}")
    print(f"{'변동성':<25} {traditional_analysis['volatility']:>14.2%} {risk_aware_analysis['volatility']:>14.2%}")
    print(f"{'샤프 비율':<25} {traditional_analysis['sharpe_ratio']:>14.2f} {risk_aware_analysis['sharpe_ratio']:>14.2f}")
    print(f"{'VaR (95%)':<25} {traditional_analysis['var_95']:>14.2%} {risk_aware_analysis['var_95']:>14.2%}")
    print(f"{'신용 점수':<25} {traditional_analysis['credit_score']:>14.1f} {risk_aware_analysis['credit_score']:>14.1f}")
    print(f"{'유동성 점수':<25} {traditional_analysis['liquidity_score']:>14.1f} {risk_aware_analysis['liquidity_score']:>14.1f}")
    print(f"{'종합 위험 점수':<25} {traditional_analysis['composite_risk_score']:>14.1f} {risk_aware_analysis['composite_risk_score']:>14.1f}")
    print(f"{'위험조정수익률':<25} {traditional_analysis['risk_adjusted_return']:>14.3f} {risk_aware_analysis['risk_adjusted_return']:>14.3f}")
    print("-" * 70)

    # 6. 개별 종목 위험 분석
    print_section("개별 종목 위험 분석 (상위 5개)")
    print("\n" + "-" * 90)
    print(f"{'종목명':<15} {'섹터':<12} {'신용점수':>10} {'유동성점수':>12} {'변동성':>10}")
    print("-" * 90)

    # 위험 인식 포트폴리오의 상위 종목만 출력
    weights_dict = risk_aware_portfolio.get_weights_dict()
    sorted_stocks = sorted(
        [(stock, weights_dict[stock.ticker]) for stock in risk_aware_portfolio.stocks],
        key=lambda x: x[1],
        reverse=True
    )[:5]

    for stock, weight in sorted_stocks:
        credit_score = CreditRiskAnalyzer.credit_score(stock)
        liquidity_score = LiquidityRiskAnalyzer.liquidity_score(stock)
        volatility = stock.volatility()
        print(f"{stock.name:<15} {stock.sector:<12} {credit_score:>10.1f} {liquidity_score:>12.1f} {volatility:>9.2%}")
    print("-" * 90)

    # 7. 권장 사항
    print_section("투자 권장 사항")
    print("""
1. 위험 관리 중심 투자자:
   - '위험 인식 포트폴리오' 전략을 권장합니다.
   - 신용 위험과 유동성 위험을 동시에 관리하여 더 안정적입니다.
   - 시장 충격 시에도 빠른 청산이 가능합니다.

2. 수익률 중심 투자자:
   - '샤프 비율 최대화' 전략을 고려할 수 있습니다.
   - 다만, 유동성이 낮은 종목의 비중이 높을 수 있으므로 주의가 필요합니다.

3. 공통 권장사항:
   - 정기적으로 포트폴리오를 리밸런싱하세요 (분기별 권장).
   - 시장 상황 변화에 따라 위험 가중치를 조정하세요.
   - 개별 종목의 신용등급 변화를 모니터링하세요.
   - 거래량이 급감하는 종목은 조기에 정리하는 것을 고려하세요.
    """)

    print_section("분석 완료")
    print("\n모든 분석이 완료되었습니다.")
    print("실제 투자 시에는 최신 시장 데이터를 사용하시기 바랍니다.\n")


if __name__ == "__main__":
    main()
