"""
포트폴리오 추천 및 리밸런싱 - 올인원 스크립트

기능:
1. 종목 추천 시스템
   - 대형주 15개 (기본) 또는 KOSPI 시가총액 상위 100개
   - 외국인 순매수(40%) + 기관 순매수(30%) + 거래량(30%)
2. 상위 5개 종목 추천
3. 포트폴리오 리밸런싱 (차등 비중: 30%, 25%, 20%, 15%, 10%)
4. 매수/매도 추천 (표 형식)

설정:
- USE_ALL_KOSPI: False (대형주 15개) / True (KOSPI 상위 100개)
- TOP_N: 추천 종목 수 (기본 5개)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.api.krx_client import KRXAPIClient
from src.advisor.manual_trading_advisor import ManualTradingAdvisor
from src.strategies.momentum import MomentumStrategy
from src.models.korean_stock import KoreanStock, TradingData
from datetime import datetime, timedelta


def get_top_stocks(api_client: KRXAPIClient, count: int = 5, use_all_kospi: bool = False):
    """
    추천 종목 선정

    Args:
        api_client: API 클라이언트
        count: 추천 종목 수
        use_all_kospi: True면 전체 KOSPI, False면 대형주만

    Returns:
        추천 종목 티커 리스트
    """
    print("\n" + "="*90)
    print("  📊 종목 추천 시스템")
    print("="*90)

    if use_all_kospi:
        # pykrx로 전체 KOSPI 종목 가져오기
        print("\n전체 KOSPI 종목 조회 중...")
        try:
            from datetime import datetime
            from pykrx import stock

            today = datetime.now().strftime("%Y%m%d")
            all_tickers = stock.get_market_ticker_list(date=today, market="KOSPI")

            # 시가총액 상위 100개만 (너무 많으면 느림)
            market_cap_df = stock.get_market_cap(date=today, market="KOSPI")
            market_cap_df = market_cap_df.sort_values('시가총액', ascending=False)
            candidate_tickers = market_cap_df.head(100).index.tolist()

            print(f"✅ KOSPI 시가총액 상위 100개 종목 선정")
            candidate_stocks = {}  # 종목명은 API로 조회

        except Exception as e:
            print(f"⚠️  전체 KOSPI 조회 실패: {e}")
            print("   대형주 15개로 폴백합니다...")
            use_all_kospi = False

    if not use_all_kospi:
        # 대형주 15개 (폴백 또는 기본 모드)
        candidate_stocks = {
            "005930": "삼성전자",
            "000660": "SK하이닉스",
            "035420": "NAVER",
            "035720": "카카오",
            "207940": "삼성바이오",
            "005380": "현대차",
            "000270": "기아",
            "051910": "LG화학",
            "006400": "삼성SDI",
            "068270": "셀트리온",
            "105560": "KB금융",
            "055550": "신한지주",
            "096770": "SK이노베이션",
            "012330": "현대모비스",
            "028260": "삼성물산",
        }
        candidate_tickers = list(candidate_stocks.keys())
        print(f"대형주 {len(candidate_tickers)}개 종목 분석")

    print(f"\n후보 종목: {len(candidate_tickers)}개")
    print("분석 기준: 거래량(30%) + 외국인 순매수(40%) + 기관 순매수(30%)")

    # 시세 조회
    stocks_data = []
    print(f"\n📈 시세 조회 중...")

    for ticker in candidate_tickers:
        market_data = api_client.get_market_data(ticker)
        if not market_data:
            continue

        # 종목명 가져오기
        if use_all_kospi or ticker not in candidate_stocks:
            # pykrx로 종목명 조회
            try:
                name = str(api_client.get_ticker_name(ticker))
                if not name or name == ticker:
                    name = ticker
            except:
                name = ticker
        else:
            # 하드코딩된 매핑 사용
            name = candidate_stocks.get(ticker, ticker)

        # 종합 점수 계산
        # 1. 거래량 점수 (거래 활발도)
        volume_score = market_data.volume / 1000000

        # 2. 외국인 순매수 점수
        foreign_net = market_data.foreign_buy - market_data.foreign_sell
        foreign_score = foreign_net / 100000 if market_data.volume > 0 else 0

        # 3. 기관 순매수 점수
        institution_net = market_data.institution_buy - market_data.institution_sell
        institution_score = institution_net / 100000 if market_data.volume > 0 else 0

        # 종합 점수 (거래량 30% + 외국인 40% + 기관 30%)
        score = (volume_score * 0.3 + foreign_score * 0.4 + institution_score * 0.3)

        stocks_data.append({
            'ticker': ticker,
            'name': name,
            'price': market_data.price,
            'volume': market_data.volume,
            'foreign_net': foreign_net,
            'institution_net': institution_net,
            'score': score
        })

    # 점수 기준 정렬
    stocks_data.sort(key=lambda x: x['score'], reverse=True)

    # 상위 N개 선정
    top_stocks = stocks_data[:count]

    print(f"\n✅ 추천 종목 (상위 {count}개)")
    print("="*100)
    print(f"  {'순위':4} {'종목코드':10} {'종목명':15} {'현재가':>12} {'거래량':>15} {'외국인':>12} {'기관':>12}")
    print("  " + "-"*96)

    for i, stock in enumerate(top_stocks, 1):
        foreign_icon = "📈" if stock['foreign_net'] > 0 else "📉" if stock['foreign_net'] < 0 else "➖"
        institution_icon = "📈" if stock['institution_net'] > 0 else "📉" if stock['institution_net'] < 0 else "➖"

        print(f"  {i:4} {stock['ticker']:10} {stock['name']:15} "
              f"{stock['price']:>12,.0f}원 {stock['volume']:>15,}주 "
              f"{foreign_icon}{abs(stock['foreign_net']):>10,}주 "
              f"{institution_icon}{abs(stock['institution_net']):>10,}주")

    return [s['ticker'] for s in top_stocks]


def main():
    # ========== 설정 ==========
    USE_ALL_KOSPI = False  # True: KOSPI 시가총액 상위 100개, False: 대형주 15개
    TOP_N = 5  # 추천 종목 수
    # ==========================

    print("="*90)
    print("  🚀 포트폴리오 추천 및 리밸런싱 시스템")
    print("="*90)

    # 1. API 연결
    print("\n[1단계] KRX API 연결...")
    api_client = KRXAPIClient(position_file="data/my_positions.json")
    api_client.connect()

    # 2. 종목 추천
    print("\n[2단계] 종목 추천...")
    recommended_tickers = get_top_stocks(api_client, count=TOP_N, use_all_kospi=USE_ALL_KOSPI)

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
