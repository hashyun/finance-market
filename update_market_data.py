"""
pykrx로 최신 시세 데이터를 다운로드해서 CSV 파일 업데이트
"""
import os
import sys
from datetime import datetime, timedelta

try:
    from pykrx import stock
except ImportError:
    print("❌ pykrx가 설치되어 있지 않습니다.")
    print("   설치: pip install pykrx")
    sys.exit(1)


def update_csv_data(ticker, days=30):
    """
    특정 종목의 최신 데이터를 CSV로 저장

    Args:
        ticker: 종목코드
        days: 조회 일수
    """
    print(f"\n📊 {ticker} 데이터 업데이트 중...")

    try:
        # 최근 N일 데이터 조회
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        end_str = end_date.strftime("%Y%m%d")
        start_str = start_date.strftime("%Y%m%d")

        # OHLCV 데이터 조회
        df = stock.get_market_ohlcv_by_date(start_str, end_str, ticker)

        if df.empty:
            print(f"   ❌ 데이터 없음 (종목코드 확인: {ticker})")
            return False

        # 종목명 조회
        try:
            name = stock.get_market_ticker_name(ticker)
            print(f"   종목명: {name}")
        except:
            name = ticker

        # 최신 데이터 확인
        latest_date = df.index[-1]
        latest_price = df.iloc[-1]['종가']
        print(f"   최신 데이터: {latest_date.strftime('%Y-%m-%d')} - {latest_price:,.0f}원")

        # CSV 파일 저장
        csv_dir = "data/market_data"
        os.makedirs(csv_dir, exist_ok=True)

        csv_file = f"{csv_dir}/{ticker}.csv"

        # DataFrame 변환 (영문 컬럼명)
        df_export = df.copy()
        df_export.index.name = 'Date'
        df_export.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

        # Change 컬럼 계산 (전일 대비)
        df_export['Change'] = df_export['Close'].diff()
        df_export['Change'] = df_export['Change'].apply(
            lambda x: f"+{int(x)}" if x > 0 else str(int(x)) if not pd.isna(x) else "0"
        )

        # CSV 저장
        df_export.to_csv(csv_file, encoding='utf-8')

        print(f"   ✅ 저장 완료: {csv_file}")
        print(f"   데이터 개수: {len(df_export)}개")

        return True

    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return False


def main():
    print("=" * 70)
    print("  시세 데이터 업데이트 (pykrx → CSV)")
    print("=" * 70)

    # 업데이트할 종목 리스트
    tickers = [
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
    ]

    print(f"\n총 {len(tickers)}개 종목 업데이트")
    print("조회 기간: 최근 30거래일")

    success_count = 0

    for ticker in tickers:
        if update_csv_data(ticker, days=30):
            success_count += 1

    print("\n" + "=" * 70)
    print(f"✅ 업데이트 완료: {success_count}/{len(tickers)}개 종목")
    print("=" * 70)

    if success_count > 0:
        print("\n이제 test_csv_data.py를 실행하면 최신 데이터를 사용합니다!")


if __name__ == "__main__":
    # pandas import (pykrx가 사용)
    import pandas as pd
    main()
