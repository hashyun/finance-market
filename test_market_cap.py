"""
시가총액 상위 종목 조회 테스트
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.api.krx_client import KRXAPIClient

def test_market_cap():
    """시가총액 상위 종목 조회 테스트"""
    print("=" * 80)
    print("시가총액 상위 종목 조회 테스트")
    print("=" * 80)

    # KRX API 클라이언트 초기화
    api_client = KRXAPIClient()

    # KOSPI 시가총액 상위 20개
    print("\n[KOSPI 시가총액 상위 20개]")
    top_20_kospi = api_client.get_top_tickers_by_market_cap(top_n=20, market="KOSPI")

    if top_20_kospi:
        print(f"총 {len(top_20_kospi)}개 종목 조회됨\n")
        for i, ticker in enumerate(top_20_kospi[:20], 1):
            name = api_client.get_ticker_name(ticker)
            print(f"{i:2}. {ticker} - {name}")
    else:
        print("❌ 종목 조회 실패")

    # KOSDAQ 시가총액 상위 10개
    print("\n" + "=" * 80)
    print("[KOSDAQ 시가총액 상위 10개]")
    top_10_kosdaq = api_client.get_top_tickers_by_market_cap(top_n=10, market="KOSDAQ")

    if top_10_kosdaq:
        print(f"총 {len(top_10_kosdaq)}개 종목 조회됨\n")
        for i, ticker in enumerate(top_10_kosdaq[:10], 1):
            name = api_client.get_ticker_name(ticker)
            print(f"{i:2}. {ticker} - {name}")
    else:
        print("❌ 종목 조회 실패")

    print("\n" + "=" * 80)
    print("테스트 완료")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_market_cap()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
