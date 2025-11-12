"""
실시간 트레이딩 시스템 통합 예제
- 실시간 데이터 연동
- 자동 리밸런싱
- 실시간 알림
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.api.mock_client import MockAPIClient
from src.strategies.foreign_follow import ForeignFollowStrategy
from src.strategies.momentum import MomentumStrategy
from src.strategies.multi_strategy import MultiStrategy
from src.rebalance.rebalancer import PortfolioRebalancer
from src.notification.notifier import Notifier, NotificationLevel
from src.notification.channels import ConsoleChannel, FileChannel


def print_section(title):
    """섹션 제목 출력"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_account_status(api_client: MockAPIClient):
    """계좌 상태 출력"""
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
        print("  " + "-" * 75)

        for ticker, holding in holdings.items():
            print(f"  {ticker:10} "
                  f"{holding['quantity']:>10,}주 "
                  f"{holding['avg_price']:>12,.0f}원 "
                  f"{holding['current_price']:>12,.0f}원 "
                  f"{holding['profit_loss']:>15,.0f}원 "
                  f"{holding['profit_loss_pct']:>9.2f}%")


def print_market_data(api_client: MockAPIClient, tickers: list):
    """실시간 시세 출력"""
    print("\n[실시간 시세]")
    print(f"  {'종목':10} {'현재가':>12} {'외국인순매수':>15} {'기관순매수':>15}")
    print("  " + "-" * 60)

    market_data_batch = api_client.get_market_data_batch(tickers)

    for ticker, data in market_data_batch.items():
        print(f"  {ticker:10} "
              f"{data.price:>12,.0f}원 "
              f"{data.foreign_net:>15,}주 "
              f"{data.institution_net:>15,}주")


def run_realtime_trading_system(duration_seconds: int = 30, check_interval: int = 5):
    """
    실시간 트레이딩 시스템 실행

    Args:
        duration_seconds: 실행 시간 (초)
        check_interval: 체크 주기 (초)
    """
    print_section("실시간 트레이딩 시스템 시작")

    # 1. API 클라이언트 초기화
    print("\n[1단계] API 연결...")
    api_client = MockAPIClient(initial_balance=100_000_000)
    api_client.connect()

    # 2. 알림 시스템 초기화
    print("\n[2단계] 알림 시스템 초기화...")
    notifier = Notifier()
    notifier.add_channel(ConsoleChannel(colored=True))
    notifier.add_channel(FileChannel(log_file="logs/trading.log"))

    notifier.info("시스템 시작", "실시간 트레이딩 시스템이 시작되었습니다.")

    # 3. 트레이딩 전략 설정
    print("\n[3단계] 트레이딩 전략 설정...")
    foreign_strategy = ForeignFollowStrategy()
    momentum_strategy = MomentumStrategy()

    multi_strategy = MultiStrategy(
        strategies=[foreign_strategy, momentum_strategy],
        weights=[0.6, 0.4]
    )

    print("  전략: 외국인 수급 60% + 모멘텀 40%")

    # 4. 대상 종목 설정
    target_tickers = ['005930', '000660', '035420', '035720', '068270']

    print(f"\n[4단계] 대상 종목: {', '.join(target_tickers)}")

    # 5. 리밸런서 초기화
    print("\n[5단계] 자동 리밸런서 초기화...")
    rebalancer = PortfolioRebalancer(
        api_client=api_client,
        strategy=multi_strategy,
        target_tickers=target_tickers,
        rebalance_threshold=0.05,  # 5% 이상 벗어나면 리밸런싱
        min_trade_amount=100_000,  # 최소 10만원
        max_position_size=0.3  # 최대 30%
    )

    print("  리밸런싱 임계값: 5%")
    print("  최소 거래 금액: 100,000원")
    print("  최대 포지션 크기: 30%")

    # 6. 초기 포트폴리오 구성
    print("\n[6단계] 초기 포트폴리오 구성...")
    notifier.info("초기 포트폴리오 구성 시작", "목표 비중에 맞춰 초기 매수를 진행합니다.")

    # 목표 비중 계산
    target_weights = rebalancer.calculate_target_weights()

    print("  목표 비중:")
    for ticker, weight in target_weights.items():
        print(f"    {ticker}: {weight:.1%}")

    # 초기 매수 실행
    account = api_client.get_account_balance()
    total_value = account['total_value']

    for ticker, weight in target_weights.items():
        if weight > 0:
            market_data = api_client.get_market_data(ticker)
            if market_data:
                target_value = total_value * weight
                quantity = int(target_value / market_data.price)

                if quantity > 0:
                    from src.api.base_client import OrderRequest

                    order = OrderRequest(
                        ticker=ticker,
                        order_type="BUY",
                        quantity=quantity,
                        order_method="MARKET"
                    )

                    response = api_client.place_order(order)

                    if response.status == "SUCCESS":
                        notifier.info(
                            f"초기 매수: {ticker}",
                            f"{quantity}주를 {response.price:,.0f}원에 매수했습니다.",
                            {'ticker': ticker, 'quantity': quantity, 'price': response.price}
                        )

    # 초기 계좌 상태
    print_account_status(api_client)

    # 7. 실시간 모니터링 시작
    print_section("실시간 모니터링 시작")
    print(f"\n{duration_seconds}초 동안 {check_interval}초마다 체크합니다...")

    notifier.info("모니터링 시작", f"{duration_seconds}초 동안 실시간 모니터링을 시작합니다.")

    start_time = time.time()
    check_count = 0

    try:
        while time.time() - start_time < duration_seconds:
            check_count += 1

            print_section(f"체크 #{check_count}")

            # 실시간 시세 조회
            print_market_data(api_client, target_tickers)

            # 리밸런싱 필요 여부 확인
            preview = rebalancer.get_rebalancing_preview()

            print("\n[리밸런싱 분석]")
            print(f"  리밸런싱 필요: {'예' if preview['needs_rebalancing'] else '아니오'}")

            if preview['needs_rebalancing']:
                print("\n  비중 변화:")
                for ticker, info in preview['deviations'].items():
                    if abs(info['deviation']) > 0.01:  # 1% 이상 차이
                        print(f"    {ticker}: {info['current']:.1%} → {info['target']:.1%} "
                              f"({'매수' if info['action'] == 'BUY' else '매도' if info['action'] == 'SELL' else '유지'})")

                # 리밸런싱 실행
                notifier.warning("리밸런싱 필요", "포트폴리오 비중이 목표에서 벗어났습니다. 리밸런싱을 시작합니다.")

                result = rebalancer.run_rebalancing_check()

                if result and result.success:
                    notifier.alert(
                        "리밸런싱 완료",
                        result.message,
                        {'orders': len(result.orders_executed)}
                    )

                    print(f"\n  ✅ 리밸런싱 완료: {len(result.orders_executed)}개 주문 실행")

                    for order in result.orders_executed:
                        if order['status'] == 'SUCCESS':
                            action = "매수" if order['order_type'] == 'BUY' else "매도"
                            print(f"     - {action}: {order['ticker']} {order['quantity']:,}주 @ {order['price']:,.0f}원")
                elif result:
                    notifier.error("리밸런싱 실패", result.message)
                    print(f"\n  ❌ 리밸런싱 실패: {result.message}")

            # 계좌 상태
            print_account_status(api_client)

            # 다음 체크까지 대기
            if time.time() - start_time < duration_seconds:
                print(f"\n⏱️  다음 체크까지 {check_interval}초 대기 중...")
                time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\n\n사용자가 중단했습니다.")
        notifier.warning("시스템 중단", "사용자가 시스템을 중단했습니다.")

    # 8. 최종 결과
    print_section("최종 결과")

    final_account = api_client.get_account_balance()

    print("\n[최종 성과]")
    print(f"  초기 자본:        {api_client.initial_balance:>15,.0f}원")
    print(f"  최종 자산:        {final_account['total_value']:>15,.0f}원")
    print(f"  총 손익:          {final_account['profit_loss']:>15,.0f}원")
    print(f"  수익률:           {final_account['profit_loss_pct']:>14.2f}%")

    notifier.info(
        "시스템 종료",
        f"실시간 트레이딩 시스템을 종료합니다. 최종 수익률: {final_account['profit_loss_pct']:.2f}%",
        final_account
    )

    # 알림 히스토리
    print("\n[알림 히스토리]")
    history = notifier.get_history(limit=10)

    for notification in history[-5:]:  # 최근 5개만
        print(f"  [{notification.level.value}] {notification.title}")

    print(f"\n  총 {len(history)}개의 알림이 전송되었습니다.")
    print(f"  로그 파일: logs/trading.log")

    # API 연결 해제
    api_client.disconnect()

    print_section("시스템 종료 완료")


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║              한국 주식 실시간 트레이딩 시스템                                ║
║                                                                            ║
║  • 실시간 데이터 연동                                                        ║
║  • 자동 포트폴리오 리밸런싱                                                   ║
║  • 실시간 알림 시스템                                                        ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    try:
        # 30초 동안 5초마다 체크
        run_realtime_trading_system(duration_seconds=30, check_interval=5)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
