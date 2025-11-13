"""
포트폴리오 리밸런싱 추천 테스트
현재 CSV 데이터로 자동 실행
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.api.krx_client import KRXAPIClient
from src.advisor.manual_trading_advisor import ManualTradingAdvisor
from src.strategies.momentum import MomentumStrategy


def main():
    print("=" * 80)
    print("  포트폴리오 리밸런싱 추천 시스템")
    print("=" * 80)

    # KRX API 클라이언트 초기화
    print("\n[1단계] API 연결...")
    api_client = KRXAPIClient(position_file="data/my_positions.json")
    api_client.connect()

    # 계좌 상태 조회
    print("\n[2단계] 현재 포트폴리오 상태")
    account = api_client.get_account_balance()
    holdings = api_client.get_holdings()

    print("\n[계좌 현황]")
    print(f"  현금 잔고:        {account['cash_balance']:>15,.0f}원")
    print(f"  주식 평가액:      {account['stock_value']:>15,.0f}원")
    print(f"  총 자산:          {account['total_value']:>15,.0f}원")
    print(f"  손익:             {account['profit_loss']:>15,.0f}원 ({account['profit_loss_pct']:+.2f}%)")

    if holdings:
        print("\n[보유 종목]")
        print(f"  {'종목':10} {'수량':>10} {'평균단가':>12} {'현재가':>12} {'평가손익':>12} {'수익률':>10}")
        print("  " + "-" * 75)

        for ticker, holding in holdings.items():
            name = api_client.positions['holdings'][ticker].get('name', ticker)
            print(f"  {name:10} "
                  f"{holding['quantity']:>10,}주 "
                  f"{holding['avg_price']:>12,.0f}원 "
                  f"{holding['current_price']:>12,.0f}원 "
                  f"{holding['profit_loss']:>12,.0f}원 "
                  f"{holding['profit_loss_pct']:>9.2f}%")

    # 전략 설정
    print("\n[3단계] 트레이딩 전략 설정")
    strategy = MomentumStrategy()
    print("  전략: 모멘텀 전략")

    # 대상 종목
    target_tickers = list(holdings.keys()) if holdings else ['005930', '000660', '035420']
    print(f"  대상 종목: {', '.join(target_tickers)}")

    # 어드바이저 초기화
    print("\n[4단계] 리밸런싱 분석 중...")
    advisor = ManualTradingAdvisor(
        api_client=api_client,
        strategy=strategy,
        target_tickers=target_tickers,
        rebalance_threshold=0.05,  # 5%
        min_trade_amount=100_000,
        max_position_size=0.3  # 30%로 설정 (5개 종목 차등 배분)
    )

    # 매매 가이드 출력
    advisor.print_trading_guide()

    # 추천 저장
    print("\n[5단계] 추천 저장")
    advisor.export_recommendations_to_file("data/trading_recommendations.json")

    print("\n" + "=" * 80)
    print("  분석 완료!")
    print("=" * 80)

    api_client.disconnect()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
