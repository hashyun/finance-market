"""
한국 시장 알고리즘 트레이딩 예제
외국인 매매, 기관 매매 등 한국 시장 특성을 반영한 전략 테스트
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.data_generator import KoreanDataGenerator
from src.strategies.foreign_follow import ForeignFollowStrategy
from src.strategies.momentum import MomentumStrategy
from src.strategies.mean_reversion import MeanReversionStrategy
from src.strategies.multi_strategy import MultiStrategy
from src.backtest.backtester import Backtester
from src.analysis.investor_flow import InvestorFlowAnalyzer
from src.analysis.market_indicators import KoreanMarketIndicators


def print_section(title):
    """섹션 제목 출력"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_stock_analysis(stock):
    """종목 분석 출력"""
    print(f"\n[{stock.name} ({stock.ticker}) - {stock.market}]")

    # 투자자 수급 분석
    flow_analysis = InvestorFlowAnalyzer.analyze_investor_flow(stock)

    print("\n<투자자 수급>")
    print(f"  외국인 매수 강도:     {flow_analysis['foreign_strength']:>6.1f}")
    print(f"  기관 매수 강도:       {flow_analysis['institution_strength']:>6.1f}")
    print(f"  개인 매수 강도:       {flow_analysis['individual_strength']:>6.1f}")
    print(f"  컨센서스 점수:        {flow_analysis['consensus_score']:>6.1f}")
    print(f"  외국인 추세:          {flow_analysis['foreign_trend']:>10s}")
    print(f"  프로그램 매매 신호:   {flow_analysis['program_signal']:>6.1f}")
    print(f"  숏스퀴즈 가능성:      {flow_analysis['short_squeeze_potential']:>6.1f}")
    print(f"  종합 점수:            {flow_analysis['total_score']:>6.1f}")

    # 기술적 지표
    indicators = KoreanMarketIndicators.calculate_all_indicators(stock)

    if indicators:
        print("\n<기술적 지표>")
        print(f"  현재가:               {indicators['price']:>10,.0f}원")
        print(f"  5일 이동평균:         {indicators['ma5']:>10,.0f}원")
        print(f"  20일 이동평균:        {indicators['ma20']:>10,.0f}원")
        print(f"  60일 이동평균:        {indicators['ma60']:>10,.0f}원")
        print(f"  RSI:                  {indicators['rsi']:>6.1f}")
        print(f"  MACD:                 {indicators['macd']:>10,.2f}")
        print(f"  볼린저밴드 위치:      {indicators['bb_position']:>6.1f}%")
        print(f"  스토캐스틱 K:         {indicators['stochastic_k']:>6.1f}")
        print(f"  ATR:                  {indicators['atr']:>10,.2f}")


def print_strategy_signals(stocks, strategy):
    """전략별 매매 신호 출력"""
    print(f"\n[{strategy.name} 전략 신호]")
    print("-" * 80)

    for stock in stocks:
        signal = strategy.generate_signal(stock)
        score = strategy.calculate_score(stock)

        signal_emoji = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "⚪"

        print(f"  {signal_emoji} {stock.name:15s} | 신호: {signal:>4s} | 점수: {score:>6.1f}")


def print_backtest_result(strategy_name, result):
    """백테스트 결과 출력"""
    print(f"\n[{strategy_name} 백테스트 결과]")
    print("-" * 80)
    print(f"  초기 자본:            {result.initial_capital:>15,.0f}원")
    print(f"  최종 자본:            {result.final_capital:>15,.0f}원")
    print(f"  총 수익:              {result.total_return:>15,.0f}원")
    print(f"  수익률:               {result.total_return_pct:>14.2f}%")
    print(f"  총 거래 횟수:         {result.num_trades:>15,}회")
    print(f"  승리 거래:            {result.num_wins:>15,}회")
    print(f"  손실 거래:            {result.num_losses:>15,}회")
    print(f"  승률:                 {result.win_rate:>14.2f}%")
    print(f"  최대 낙폭:            {result.max_drawdown:>14.2f}%")
    print(f"  샤프 비율:            {result.sharpe_ratio:>15.2f}")
    print("-" * 80)


def main():
    print_section("한국 시장 알고리즘 트레이딩 시스템")

    # 1. 샘플 데이터 생성
    print("\n[1단계] 한국 시장 데이터 생성...")
    print("  - 외국인/기관/개인 매매 데이터")
    print("  - 프로그램 매매 데이터")
    print("  - 공매도 데이터")
    print("  - 100일간의 거래 데이터")

    stocks = KoreanDataGenerator.generate_sample_stocks(num_days=100)

    print(f"\n  총 {len(stocks)}개 종목:")
    for stock in stocks:
        print(f"    - {stock.name} ({stock.ticker}, {stock.market})")

    # 2. 종목 분석
    print_section("개별 종목 분석")

    for stock in stocks[:3]:  # 상위 3개 종목만 상세 분석
        print_stock_analysis(stock)

    # 3. 전략별 신호 생성
    print_section("트레이딩 전략별 신호")

    # 전략 초기화
    foreign_strategy = ForeignFollowStrategy()
    momentum_strategy = MomentumStrategy()
    reversion_strategy = MeanReversionStrategy()

    # 각 전략별 신호 출력
    print_strategy_signals(stocks, foreign_strategy)
    print_strategy_signals(stocks, momentum_strategy)
    print_strategy_signals(stocks, reversion_strategy)

    # 4. 멀티 전략
    print_section("멀티 전략 (복합 전략)")

    multi_strategy = MultiStrategy(
        strategies=[foreign_strategy, momentum_strategy, reversion_strategy],
        weights=[0.5, 0.3, 0.2]  # 외국인 수급 50%, 모멘텀 30%, 평균회귀 20%
    )

    print("\n전략 구성:")
    print("  - 외국인 수급 추종:   50%")
    print("  - 모멘텀 전략:        30%")
    print("  - 평균회귀 전략:      20%")

    print_strategy_signals(stocks, multi_strategy)

    # 전략별 점수 분해 (예시: 삼성전자)
    print("\n\n[삼성전자 전략 분해 분석]")
    print("-" * 80)
    samsung = stocks[0]
    breakdown = multi_strategy.get_strategy_breakdown(samsung)

    for strategy_name, data in breakdown.items():
        if 'error' not in data:
            print(f"\n  {strategy_name}:")
            print(f"    원점수:           {data['score']:>6.1f}")
            print(f"    가중치:           {data['weight']:>6.1%}")
            print(f"    가중 점수:        {data['weighted_score']:>6.1f}")
            print(f"    신호:             {data['signal']:>6s}")

    # 5. 백테스팅
    print_section("백테스팅 결과 비교")

    backtester = Backtester(
        initial_capital=100_000_000,  # 1억원
        commission_rate=0.00015,
        tax_rate=0.0023,
        max_position_size=0.3
    )

    print("\n백테스팅 설정:")
    print("  - 초기 자본:          100,000,000원 (1억원)")
    print("  - 수수료율:           0.015%")
    print("  - 거래세:             0.23%")
    print("  - 최대 포지션 크기:   30%")
    print("  - 리밸런싱 주기:      5일")

    strategies_to_test = [
        ("외국인 수급 추종", foreign_strategy),
        ("모멘텀 전략", momentum_strategy),
        ("평균회귀 전략", reversion_strategy),
        ("멀티 전략", multi_strategy)
    ]

    results = []

    for strategy_name, strategy in strategies_to_test:
        print(f"\n{strategy_name} 백테스팅 중...")
        result = backtester.run(
            stocks=stocks,
            strategy=strategy,
            rebalance_period=5
        )
        results.append((strategy_name, result))
        print_backtest_result(strategy_name, result)

    # 6. 전략 비교
    print_section("전략 성과 비교")

    print("\n" + "-" * 90)
    print(f"{'전략명':<20} {'수익률':>10} {'승률':>10} {'샤프비율':>10} {'최대낙폭':>10} {'거래횟수':>10}")
    print("-" * 90)

    for strategy_name, result in results:
        print(f"{strategy_name:<20} "
              f"{result.total_return_pct:>9.2f}% "
              f"{result.win_rate:>9.2f}% "
              f"{result.sharpe_ratio:>10.2f} "
              f"{result.max_drawdown:>9.2f}% "
              f"{result.num_trades:>10,}회")

    print("-" * 90)

    # 7. 추천 전략
    print_section("투자 전략 추천")

    # 최고 수익률
    best_return = max(results, key=lambda x: x[1].total_return_pct)
    # 최고 샤프 비율
    best_sharpe = max(results, key=lambda x: x[1].sharpe_ratio)
    # 최고 승률
    best_winrate = max(results, key=lambda x: x[1].win_rate)

    print(f"""
1. 수익률 중심 투자자
   추천 전략: {best_return[0]}
   - 수익률: {best_return[1].total_return_pct:.2f}%
   - 특징: 높은 수익을 추구하지만 변동성도 클 수 있음

2. 위험조정 수익 중심 투자자
   추천 전략: {best_sharpe[0]}
   - 샤프 비율: {best_sharpe[1].sharpe_ratio:.2f}
   - 특징: 위험 대비 안정적인 수익 추구

3. 안정성 중심 투자자
   추천 전략: {best_winrate[0]}
   - 승률: {best_winrate[1].win_rate:.2f}%
   - 특징: 손실 거래를 최소화하는 보수적 전략

4. 한국 시장 특화 전략 특징
   - 외국인 수급: 대형주에서 효과적, 장기 추세 추종
   - 기관 매매: 중기 추세, 테마주에 효과적
   - 프로그램 매매: 단기 모멘텀 포착
   - 공매도 분석: 숏 스퀴즈 기회 발견

5. 실전 활용 팁
   - 외국인 + 기관 동시 매수: 강한 상승 신호
   - 프로그램 매수 급증: 단기 반등 기회
   - 공매도 비율 높고 외국인 매수: 숏 스퀴즈 가능
   - RSI 과매도 + 외국인 매수: 저점 매수 기회
    """)

    print_section("분석 완료")
    print("\n모든 분석이 완료되었습니다.")
    print("실제 투자 시에는 실시간 데이터와 추가적인 리스크 관리가 필요합니다.\n")


if __name__ == "__main__":
    main()
