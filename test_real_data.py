"""
실제 KRX 데이터 테스트
pykrx를 사용하여 실제 한국 주식 데이터 가져오기
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.api.krx_client import KRXAPIClient


def main():
    print("=" * 70)
    print("  실제 KRX 데이터 테스트")
    print("=" * 70)

    # KRX 클라이언트 생성
    client = KRXAPIClient()
    client.connect()

    if not client.pykrx_available:
        print("\n❌ pykrx가 설치되지 않았습니다.")
        print("   설치 명령: pip install pykrx")
        return

    print("\n[테스트 1] 삼성전자 시세 조회")
    print("-" * 70)
    samsung = client.get_market_data("005930")
    if samsung:
        print(f"  종목명: {client.get_ticker_name('005930')}")
        print(f"  현재가: {samsung.price:,.0f}원")
        print(f"  시가:   {samsung.open:,.0f}원")
        print(f"  고가:   {samsung.high:,.0f}원")
        print(f"  저가:   {samsung.low:,.0f}원")
        print(f"  거래량: {samsung.volume:,.0f}주")
        print(f"  외국인 순매수: {samsung.foreign_buy - samsung.foreign_sell:,.0f}주")
        print(f"  기관 순매수:   {samsung.institution_buy - samsung.institution_sell:,.0f}주")

    print("\n[테스트 2] 여러 종목 일괄 조회")
    print("-" * 70)
    tickers = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
        "035420",  # NAVER
        "035720",  # 카카오
        "207940",  # 삼성바이오로직스
    ]

    batch_data = client.get_market_data_batch(tickers)

    print(f"\n조회 결과: {len(batch_data)}개 종목")
    print("\n" + "-" * 70)
    print(f"{'종목명':<15} {'종목코드':<10} {'현재가':>12} {'등락':>10}")
    print("-" * 70)

    for ticker, data in batch_data.items():
        name = client.get_ticker_name(ticker)
        change = ((data.price - data.open) / data.open * 100) if data.open > 0 else 0
        change_str = f"{change:+.2f}%"
        print(f"{name:<15} {ticker:<10} {data.price:>11,.0f}원 {change_str:>10}")

    print("\n[테스트 3] 투자자 매매 동향 (최근 20일)")
    print("-" * 70)
    flow = client.get_investor_flow("005930", days=20)
    if flow:
        print(f"  외국인: {flow['foreign_net']:>15,.0f}원")
        print(f"  기관:   {flow['institution_net']:>15,.0f}원")
        print(f"  개인:   {flow['individual_net']:>15,.0f}원")

    print("\n" + "=" * 70)
    print("✅ 실제 데이터 테스트 완료!")
    print("=" * 70)


if __name__ == "__main__":
    main()
