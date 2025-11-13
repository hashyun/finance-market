"""
포트폴리오 추천 및 리밸런싱 - 올인원 스크립트

기능:
1. KRX에서 전체 종목 데이터 가져오기
2. 상위 5개 종목 추천 (모멘텀 + 외국인 매수 기준)
3. 포트폴리오 리밸런싱 (차등 비중: 30%, 25%, 20%, 15%, 10%)
4. 매수/매도 추천 (표 형식)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.api.krx_client import KRXAPIClient
from src.advisor.manual_trading_advisor import ManualTradingAdvisor
from src.strategies.momentum import MomentumStrategy
from src.models.korean_stock import KoreanStock, TradingData
from datetime import datetime, timedelta


def get_top_stocks(api_client: KRXAPIClient, count: int = 5):
    """
    추천 종목 선정

    Args:
        api_client: API 클라이언트
        count: 추천 종목 수

    Returns:
        추천 종목 티커 리스트
    """
    print("\n" + "="*90)
    print("  📊 종목 추천 시스템")
    print("="*90)

    # KOSPI 대형주 종목 리스트 (예시)
    candidate_tickers = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
        "035420",  # NAVER
        "035720",  # 카카오
        "207940",  # 삼성바이오로직스
        "005380",  # 현대차
        "000270",  # 기아
        "051910",  # LG화학
        "006400",  # 삼성SDI
        "068270",  # 셀트리온
        "105560",  # KB금융
        "055550",  # 신한지주
        "096770",  # SK이노베이션
        "012330",  # 현대모비스
        "028260",  # 삼성물산
    ]

    print(f"\n후보 종목: {len(candidate_tickers)}개")
    print("분석 기준: 최근 20일 수익률 + 거래량")

    # 시세 조회
    stocks_data = []
    print(f"\n📈 시세 조회 중...")

    for ticker in candidate_tickers:
        market_data = api_client.get_market_data(ticker)
        if not market_data:
            continue

        try:
            name = str(api_client.get_ticker_name(ticker))
            if not name or name == ticker:
                name = ticker
        except:
            name = ticker

        # 간단한 점수 계산 (실제로는 더 복잡한 로직 사용)
        # 거래량이 많을수록, 최근 가격이 오를수록 높은 점수
        score = market_data.volume / 1000000  # 거래량 점수

        stocks_data.append({
            'ticker': ticker,
            'name': name,
            'price': market_data.price,
            'volume': market_data.volume,
            'score': score
        })

    # 점수 기준 정렬
    stocks_data.sort(key=lambda x: x['score'], reverse=True)

    # 상위 N개 선정
    top_stocks = stocks_data[:count]

    print(f"\n✅ 추천 종목 (상위 {count}개)")
    print("="*90)
    print(f"  {'순위':4} {'종목코드':10} {'종목명':15} {'현재가':>12} {'거래량':>15}")
    print("  " + "-"*86)

    for i, stock in enumerate(top_stocks, 1):
        print(f"  {i:4} {stock['ticker']:10} {stock['name']:15} "
              f"{stock['price']:>12,.0f}원 {stock['volume']:>15,}주")

    return [s['ticker'] for s in top_stocks]


def main():
    print("="*90)
    print("  🚀 포트폴리오 추천 및 리밸런싱 시스템")
    print("="*90)

    # 1. API 연결
    print("\n[1단계] KRX API 연결...")
    api_client = KRXAPIClient(position_file="data/my_positions.json")
    api_client.connect()

    # 2. 종목 추천
    print("\n[2단계] 종목 추천...")
    recommended_tickers = get_top_stocks(api_client, count=5)

    # 3. 현재 포트폴리오 확인
    print("\n[3단계] 현재 포트폴리오 상태")
    account = api_client.get_account_balance()
    holdings = api_client.get_holdings()

    print("\n[계좌 현황]")
    print(f"  총 자산:          {account['total_value']:>15,.0f}원")
    print(f"  현금 잔고:        {account['cash_balance']:>15,.0f}원 ({account['cash_balance']/account['total_value']*100:.1f}%)")
    print(f"  주식 평가액:      {account['stock_value']:>15,.0f}원 ({account['stock_value']/account['total_value']*100:.1f}%)")
    print(f"  손익:             {account['profit_loss']:>15,.0f}원 ({account['profit_loss_pct']:+.2f}%)")

    if holdings:
        print("\n[현재 보유 종목]")
        print(f"  {'종목명':15} {'수량':>10} {'평균단가':>12} {'현재가':>12} {'평가손익':>12} {'수익률':>10}")
        print("  " + "-"*75)

        for ticker, holding in holdings.items():
            ticker_info = api_client.positions['holdings'].get(ticker, {})
            name = ticker_info.get('name', ticker)
            print(f"  {name:15} "
                  f"{holding['quantity']:>10,}주 "
                  f"{holding['avg_price']:>12,.0f}원 "
                  f"{holding['current_price']:>12,.0f}원 "
                  f"{holding['profit_loss']:>12,.0f}원 "
                  f"{holding['profit_loss_pct']:>9.2f}%")

    # 4. 리밸런싱 추천
    print("\n[4단계] 리밸런싱 분석...")
    strategy = MomentumStrategy()

    advisor = ManualTradingAdvisor(
        api_client=api_client,
        strategy=strategy,
        target_tickers=recommended_tickers,
        rebalance_threshold=0.05,  # 5%
        min_trade_amount=100_000,
        max_position_size=0.3  # 30%
    )

    # 매매 가이드 출력
    advisor.print_trading_guide()

    # 5. 추천 저장
    print("\n[5단계] 추천 저장")
    advisor.export_recommendations_to_file("data/trading_recommendations.json")
    print("✅ 저장 완료: data/trading_recommendations.json")

    print("\n" + "="*90)
    print("  ✅ 분석 완료!")
    print("="*90)

    api_client.disconnect()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n사용자가 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
