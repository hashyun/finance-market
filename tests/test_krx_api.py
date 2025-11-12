"""
KRX API 실제 데이터 조회 테스트
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
import json
from datetime import datetime


def test_naver_finance_basic():
    """네이버 금융 기본 시세 API 테스트"""
    print("\n" + "="*80)
    print("1. 네이버 금융 기본 시세 API 테스트")
    print("="*80)

    ticker = "005930"  # 삼성전자
    url = f"https://m.stock.naver.com/api/stock/{ticker}/basic"

    try:
        response = requests.get(url, timeout=10)
        print(f"\nURL: {url}")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 성공! 데이터 수신:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...")
            return True
        else:
            print(f"\n❌ 실패: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"\n❌ 오류: {e}")
        return False


def test_naver_finance_investor():
    """네이버 금융 투자자 매매 동향 API 테스트"""
    print("\n" + "="*80)
    print("2. 네이버 금융 투자자 매매 동향 API 테스트")
    print("="*80)

    ticker = "005930"  # 삼성전자
    url = f"https://m.stock.naver.com/api/stock/{ticker}/investor"

    try:
        response = requests.get(url, timeout=10)
        print(f"\nURL: {url}")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 성공! 데이터 수신:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...")
            return True
        else:
            print(f"\n❌ 실패: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"\n❌ 오류: {e}")
        return False


def test_alternative_apis():
    """대체 API들 테스트"""
    print("\n" + "="*80)
    print("3. 대체 API 테스트")
    print("="*80)

    apis = [
        {
            "name": "네이버 금융 - 종목 정보",
            "url": "https://finance.naver.com/item/main.naver?code=005930"
        },
        {
            "name": "다음 금융 - 시세",
            "url": "https://finance.daum.net/api/quotes/A005930"
        },
        {
            "name": "KRX 정보데이터시스템",
            "url": "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
        }
    ]

    for api in apis:
        print(f"\n테스트: {api['name']}")
        print(f"URL: {api['url']}")

        try:
            response = requests.get(api['url'], timeout=10)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                print(f"✅ 접근 가능")
            else:
                print(f"⚠️  HTTP {response.status_code}")

        except Exception as e:
            print(f"❌ 오류: {e}")


def test_krx_client():
    """실제 KRXAPIClient 테스트"""
    print("\n" + "="*80)
    print("4. KRXAPIClient 실제 테스트")
    print("="*80)

    try:
        from src.api.krx_client import KRXAPIClient

        # 테스트용 포지션 파일 없이 초기화
        api_client = KRXAPIClient(position_file="data/my_positions.json")
        api_client.connect()

        # 시세 조회 테스트
        print("\n삼성전자 시세 조회 중...")
        market_data = api_client.get_market_data('005930')

        if market_data:
            print(f"\n✅ 시세 조회 성공!")
            print(f"  종목코드: {market_data.ticker}")
            print(f"  시간: {market_data.timestamp}")
            print(f"  현재가: {market_data.price:,.0f}원")
            print(f"  거래량: {market_data.volume:,}주")
            print(f"  외국인 순매수: {market_data.foreign_net:,}주")
            print(f"  기관 순매수: {market_data.institution_net:,}주")
            print(f"  개인 순매수: {market_data.individual_net:,}주")
            return True
        else:
            print(f"\n❌ 시세 조회 실패")
            return False

    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_tickers():
    """여러 종목 조회 테스트"""
    print("\n" + "="*80)
    print("5. 여러 종목 일괄 조회 테스트")
    print("="*80)

    try:
        from src.api.krx_client import KRXAPIClient

        api_client = KRXAPIClient(position_file="data/my_positions.json")
        api_client.connect()

        tickers = ['005930', '000660', '035420']  # 삼성전자, SK하이닉스, NAVER
        ticker_names = {
            '005930': '삼성전자',
            '000660': 'SK하이닉스',
            '035420': 'NAVER'
        }

        print(f"\n조회 대상: {', '.join([f'{ticker_names[t]}({t})' for t in tickers])}")

        market_data_batch = api_client.get_market_data_batch(tickers)

        if market_data_batch:
            print(f"\n✅ 일괄 조회 성공! ({len(market_data_batch)}개 종목)")
            print(f"\n{'종목':10} {'현재가':>12} {'거래량':>15} {'외국인순매수':>15}")
            print("-" * 60)

            for ticker, data in market_data_batch.items():
                name = ticker_names.get(ticker, ticker)
                print(f"{name:10} {data.price:>12,.0f}원 {data.volume:>15,}주 {data.foreign_net:>15,}주")

            return True
        else:
            print(f"\n❌ 일괄 조회 실패")
            return False

    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                     KRX API 실제 데이터 조회 테스트                           ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    results = []

    # 1. 네이버 금융 기본 시세 API
    results.append(("네이버 금융 기본 시세", test_naver_finance_basic()))

    # 2. 네이버 금융 투자자 매매 동향
    results.append(("네이버 금융 투자자 매매", test_naver_finance_investor()))

    # 3. 대체 API 테스트
    test_alternative_apis()

    # 4. KRXAPIClient 테스트
    results.append(("KRXAPIClient", test_krx_client()))

    # 5. 여러 종목 조회 테스트
    results.append(("여러 종목 일괄 조회", test_multiple_tickers()))

    # 결과 요약
    print("\n" + "="*80)
    print("테스트 결과 요약")
    print("="*80)

    for name, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{name:30} {status}")

    total = len(results)
    passed = sum(1 for _, success in results if success)

    print(f"\n전체: {total}개 테스트")
    print(f"성공: {passed}개")
    print(f"실패: {total - passed}개")

    if passed == total:
        print("\n🎉 모든 테스트 통과!")
    else:
        print("\n⚠️  일부 테스트 실패. API 엔드포인트를 확인해주세요.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n사용자가 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
