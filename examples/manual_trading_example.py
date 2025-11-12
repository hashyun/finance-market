"""
KRX API + 수동 매매 예제
- KRX에서 실시간 시세 가져오기
- 포지션 파일로 포트폴리오 관리
- 리밸런싱 추천 받기
- 수동 매매 가이드
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.api.krx_client import KRXAPIClient
from src.advisor.manual_trading_advisor import ManualTradingAdvisor
from src.strategies.multi_strategy import MultiStrategy
from src.strategies.foreign_follow import ForeignFollowStrategy
from src.strategies.momentum import MomentumStrategy


def print_section(title):
    """섹션 제목 출력"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║              KRX API + 수동 매매 포트폴리오 시스템                            ║
║                                                                            ║
║  • KRX에서 실시간 시세 조회                                                  ║
║  • 포지션 파일로 포트폴리오 관리                                              ║
║  • 자동 리밸런싱 추천                                                        ║
║  • 수동 매매 가이드 제공                                                     ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    print_section("1단계: 포지션 파일 확인")

    position_file = "data/my_positions.json"

    print(f"\n포지션 파일: {position_file}")
    print("\n포지션 파일 형식:")
    print("""
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
    }
  }
}
    """)

    input("\n포지션 파일을 확인하셨으면 Enter를 눌러주세요...")

    print_section("2단계: KRX API 연결")

    # KRX API 클라이언트 초기화
    api_client = KRXAPIClient(position_file=position_file)
    api_client.connect()

    print_section("3단계: 현재 포트폴리오 상태")

    # 계좌 상태 조회
    account = api_client.get_account_balance()
    holdings = api_client.get_holdings()

    print("\n[계좌 현황]")
    print(f"  현금 잔고:        {account['cash_balance']:>15,.0f}원")
    print(f"  주식 평가액:      {account['stock_value']:>15,.0f}원")
    print(f"  총 자산:          {account['total_value']:>15,.0f}원")
    print(f"  손익:             {account['profit_loss']:>15,.0f}원 ({account['profit_loss_pct']:+.2f}%)")

    if holdings:
        print("\n[보유 종목]")
        print(f"  {'종목':10} {'수량':>10} {'평균단가':>12} {'현재가':>12} {'평가손익':>15} {'수익률':>10}")
        print("  " + "-"*75)

        for ticker, holding in holdings.items():
            print(f"  {ticker:10} "
                  f"{holding['quantity']:>10,}주 "
                  f"{holding['avg_price']:>12,.0f}원 "
                  f"{holding['current_price']:>12,.0f}원 "
                  f"{holding['profit_loss']:>15,.0f}원 "
                  f"{holding['profit_loss_pct']:>9.2f}%")

    print_section("4단계: 트레이딩 전략 설정")

    # 전략 설정
    foreign_strategy = ForeignFollowStrategy()
    momentum_strategy = MomentumStrategy()

    multi_strategy = MultiStrategy(
        strategies=[foreign_strategy, momentum_strategy],
        weights=[0.6, 0.4]
    )

    print("\n전략: 외국인 수급 60% + 모멘텀 40%")

    print_section("5단계: 리밸런싱 분석 및 추천")

    # 대상 종목 (포지션 파일의 종목들)
    target_tickers = list(holdings.keys()) if holdings else ['005930', '000660', '035420']

    # 어드바이저 초기화
    advisor = ManualTradingAdvisor(
        api_client=api_client,
        strategy=multi_strategy,
        target_tickers=target_tickers,
        rebalance_threshold=0.05,  # 5%
        min_trade_amount=100_000,
        max_position_size=0.4
    )

    # 매매 가이드 출력
    advisor.print_trading_guide()

    print_section("6단계: 추천 저장")

    # 추천 파일로 저장
    advisor.export_recommendations_to_file("data/trading_recommendations.json")

    print("\n✅ 매매 추천이 파일로 저장되었습니다: data/trading_recommendations.json")

    print_section("7단계: 실시간 시세 모니터링")

    print("\n대상 종목의 실시간 시세:")
    print(f"  {'종목':10} {'현재가':>12} {'외국인순매수':>15} {'기관순매수':>15}")
    print("  " + "-"*60)

    market_data_batch = api_client.get_market_data_batch(target_tickers)

    for ticker, data in market_data_batch.items():
        print(f"  {ticker:10} "
              f"{data.price:>12,.0f}원 "
              f"{data.foreign_net:>15,}주 "
              f"{data.institution_net:>15,}주")

    print_section("매매 실행 가이드")

    print("""
📱 수동 매매 실행 방법:

1. 증권사 앱/HTS를 실행합니다

2. 위의 매매 추천을 참고하여 주문을 실행합니다:
   - 매도 추천 종목을 먼저 매도하여 현금을 확보하세요
   - 매도 체결 후 매수 추천 종목을 매수하세요

3. 주문 체결 후 포지션 파일을 업데이트합니다:
   - data/my_positions.json 파일을 열어서
   - 보유 수량과 평균 단가를 수정하세요
   - 현금 잔고도 함께 업데이트하세요

4. 다시 이 프로그램을 실행하여 포트폴리오를 확인합니다

💡 팁:
  - 매매 추천은 data/trading_recommendations.json에 저장되어 있습니다
  - 시장 상황을 보며 천천히 체결하세요
  - 슬리피지(체결가 차이)를 고려하여 지정가 주문을 활용하세요
  - 급등/급락 시에는 추천을 재검토하세요

⚠️  주의사항:
  - 이 시스템은 추천만 제공하며, 투자 책임은 본인에게 있습니다
  - 실시간 시세는 약간의 지연이 있을 수 있습니다
  - 매매 전 반드시 증권사 HTS에서 최신 시세를 확인하세요
    """)

    print_section("시스템 종료")

    api_client.disconnect()

    print("\n프로그램을 종료합니다.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n사용자가 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
