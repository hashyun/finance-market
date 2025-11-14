"""
FRED (Federal Reserve Economic Data) 클라이언트
미국 경제 지표 조회
"""
import os
from typing import Optional, List, Dict
from datetime import datetime
import pandas as pd
from fredapi import Fred


class FREDClient:
    """
    FRED API 클라이언트
    미국 경제 데이터 조회 (금리, GDP, 실업률 등)
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: FRED API 키 (환경변수에서 자동 로드 가능)
        """
        self.api_key = api_key or os.getenv('FRED_API_KEY')
        if not self.api_key:
            raise ValueError(
                "FRED API 키가 필요합니다. "
                "https://fred.stlouisfed.org/docs/api/api_key.html 에서 발급받으세요."
            )

        self.fred = Fred(api_key=self.api_key)

    def get_series(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.Series:
        """
        특정 경제 지표 시계열 데이터 조회

        Args:
            series_id: FRED 시리즈 ID (예: 'DGS10' - 10년 국채 수익률)
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)

        Returns:
            시계열 데이터
        """
        return self.fred.get_series(
            series_id,
            observation_start=start_date,
            observation_end=end_date
        )

    def get_treasury_yields(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, pd.Series]:
        """
        미국 국채 수익률 곡선 데이터 조회

        Args:
            start_date: 시작일
            end_date: 종료일

        Returns:
            만기별 수익률 데이터
        """
        maturities = {
            '1M': 'DGS1MO',   # 1개월
            '3M': 'DGS3MO',   # 3개월
            '6M': 'DGS6MO',   # 6개월
            '1Y': 'DGS1',     # 1년
            '2Y': 'DGS2',     # 2년
            '5Y': 'DGS5',     # 5년
            '10Y': 'DGS10',   # 10년
            '30Y': 'DGS30',   # 30년
        }

        yields = {}
        for name, series_id in maturities.items():
            try:
                yields[name] = self.get_series(series_id, start_date, end_date)
            except Exception as e:
                print(f"경고: {name} 수익률 조회 실패 - {e}")

        return yields

    def get_interest_rates(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, pd.Series]:
        """
        주요 금리 지표 조회

        Args:
            start_date: 시작일
            end_date: 종료일

        Returns:
            금리 지표 딕셔너리
        """
        rates = {
            'fed_funds': 'DFF',           # 연방기금금리
            'prime_rate': 'DPRIME',       # 프라임 레이트
            'libor_3m': 'USD3MTD156N',    # 3개월 LIBOR (historical)
        }

        results = {}
        for name, series_id in rates.items():
            try:
                results[name] = self.get_series(series_id, start_date, end_date)
            except Exception as e:
                print(f"경고: {name} 조회 실패 - {e}")

        return results

    def get_economic_indicators(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, pd.Series]:
        """
        주요 경제 지표 조회

        Args:
            start_date: 시작일
            end_date: 종료일

        Returns:
            경제 지표 딕셔너리
        """
        indicators = {
            'gdp': 'GDP',                 # GDP
            'unemployment': 'UNRATE',     # 실업률
            'cpi': 'CPIAUCSL',           # 소비자물가지수
            'pce': 'PCE',                # 개인소비지출
            'industrial_production': 'INDPRO',  # 산업생산
        }

        results = {}
        for name, series_id in indicators.items():
            try:
                results[name] = self.get_series(series_id, start_date, end_date)
            except Exception as e:
                print(f"경고: {name} 조회 실패 - {e}")

        return results

    def get_credit_spreads(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, pd.Series]:
        """
        신용 스프레드 조회

        Args:
            start_date: 시작일
            end_date: 종료일

        Returns:
            신용 스프레드 데이터
        """
        spreads = {
            'baa_spread': 'BAA10Y',      # BAA 등급 스프레드
            'aaa_spread': 'AAA10Y',      # AAA 등급 스프레드
        }

        results = {}
        for name, series_id in spreads.items():
            try:
                results[name] = self.get_series(series_id, start_date, end_date)
            except Exception as e:
                print(f"경고: {name} 조회 실패 - {e}")

        return results

    def search_series(self, search_text: str, limit: int = 10) -> pd.DataFrame:
        """
        시리즈 검색

        Args:
            search_text: 검색어
            limit: 결과 개수 제한

        Returns:
            검색 결과
        """
        return self.fred.search(search_text, limit=limit)
