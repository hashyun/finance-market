"""
ECOS (한국은행 경제통계) 클라이언트
한국 경제 지표 조회
"""
import os
import requests
from typing import Optional, Dict, List
import pandas as pd
from datetime import datetime


class ECOSClient:
    """
    한국은행 경제통계시스템(ECOS) API 클라이언트
    """

    BASE_URL = "https://ecos.bok.or.kr/api"

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: ECOS API 키 (환경변수에서 자동 로드 가능)
        """
        self.api_key = api_key or os.getenv('ECOS_API_KEY')
        if not self.api_key:
            raise ValueError(
                "ECOS API 키가 필요합니다. "
                "https://ecos.bok.or.kr/api/# 에서 발급받으세요."
            )

    def _make_request(
        self,
        stat_code: str,
        cycle_type: str,
        start_date: str,
        end_date: str,
        item_code: str = "*"
    ) -> List[Dict]:
        """
        ECOS API 요청

        Args:
            stat_code: 통계표 코드
            cycle_type: 주기 (D:일, M:월, Q:분기, Y:년)
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            item_code: 항목 코드

        Returns:
            API 응답 데이터
        """
        url = f"{self.BASE_URL}/StatisticSearch/{self.api_key}/json/kr/1/10000/{stat_code}/{cycle_type}/{start_date}/{end_date}/{item_code}"

        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
            return data['StatisticSearch']['row']

        return []

    def get_base_rate(
        self,
        start_date: str = "20200101",
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        한국은행 기준금리 조회

        Args:
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)

        Returns:
            기준금리 데이터
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        # 통계표: 722 - 한국은행 기준금리
        data = self._make_request("722", "D", start_date, end_date)

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df['TIME'] = pd.to_datetime(df['TIME'], format='%Y%m%d')
        df['DATA_VALUE'] = pd.to_numeric(df['DATA_VALUE'])

        return df[['TIME', 'DATA_VALUE']].rename(
            columns={'TIME': 'date', 'DATA_VALUE': 'base_rate'}
        )

    def get_exchange_rate(
        self,
        currency: str = "USD",
        start_date: str = "20200101",
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        환율 조회

        Args:
            currency: 통화 코드 (USD, EUR, JPY, CNY 등)
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)

        Returns:
            환율 데이터
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        # 통계표: 731Y001 - 주요국 통화의 대원화 환율
        # 항목코드: 0000001 (미 달러)
        item_codes = {
            'USD': '0000001',
            'JPY': '0000002',
            'EUR': '0000003',
            'CNY': '0000004'
        }

        item_code = item_codes.get(currency, '0000001')
        data = self._make_request("731Y001", "D", start_date, end_date, item_code)

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df['TIME'] = pd.to_datetime(df['TIME'], format='%Y%m%d')
        df['DATA_VALUE'] = pd.to_numeric(df['DATA_VALUE'])

        return df[['TIME', 'DATA_VALUE']].rename(
            columns={'TIME': 'date', 'DATA_VALUE': f'{currency}_rate'}
        )

    def get_cpi(
        self,
        start_date: str = "20200101",
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        소비자물가지수(CPI) 조회

        Args:
            start_date: 시작일 (YYYYMM)
            end_date: 종료일 (YYYYMM)

        Returns:
            CPI 데이터
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m")

        # 통계표: 901Y009 - 소비자물가지수
        data = self._make_request("901Y009", "M", start_date[:6], end_date[:6], "0")

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df['TIME'] = pd.to_datetime(df['TIME'], format='%Y%m')
        df['DATA_VALUE'] = pd.to_numeric(df['DATA_VALUE'])

        return df[['TIME', 'DATA_VALUE']].rename(
            columns={'TIME': 'date', 'DATA_VALUE': 'cpi'}
        )

    def get_gdp(
        self,
        start_date: str = "202001",
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        GDP 조회

        Args:
            start_date: 시작일 (YYYYQ)
            end_date: 종료일 (YYYYQ)

        Returns:
            GDP 데이터
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y") + "Q4"

        # 통계표: 200Y001 - 국내총생산
        data = self._make_request("200Y001", "Q", start_date, end_date, "10101")

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df['DATA_VALUE'] = pd.to_numeric(df['DATA_VALUE'])

        return df[['TIME', 'DATA_VALUE']].rename(
            columns={'TIME': 'quarter', 'DATA_VALUE': 'gdp'}
        )

    def get_bond_yields(
        self,
        start_date: str = "20200101",
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        국고채 수익률 조회

        Args:
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)

        Returns:
            국고채 수익률 데이터
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        # 통계표: 817Y002 - 국고채 수익률
        # 항목: 5010000 (3년), 5020000 (5년), 5030000 (10년)
        maturities = {
            '3Y': '5010000',
            '5Y': '5020000',
            '10Y': '5030000'
        }

        results = []
        for name, item_code in maturities.items():
            data = self._make_request("817Y002", "D", start_date, end_date, item_code)
            if data:
                df = pd.DataFrame(data)
                df['TIME'] = pd.to_datetime(df['TIME'], format='%Y%m%d')
                df['DATA_VALUE'] = pd.to_numeric(df['DATA_VALUE'])
                df['maturity'] = name
                results.append(df[['TIME', 'DATA_VALUE', 'maturity']])

        if not results:
            return pd.DataFrame()

        return pd.concat(results, ignore_index=True).rename(
            columns={'TIME': 'date', 'DATA_VALUE': 'yield'}
        )

    def get_money_supply(
        self,
        start_date: str = "202001",
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        통화량(M2) 조회

        Args:
            start_date: 시작일 (YYYYMM)
            end_date: 종료일 (YYYYMM)

        Returns:
            통화량 데이터
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m")

        # 통계표: 101Y003 - 통화량(평잔, 계절조정계열)
        data = self._make_request("101Y003", "M", start_date, end_date, "BBMA00")

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df['TIME'] = pd.to_datetime(df['TIME'], format='%Y%m')
        df['DATA_VALUE'] = pd.to_numeric(df['DATA_VALUE'])

        return df[['TIME', 'DATA_VALUE']].rename(
            columns={'TIME': 'date', 'DATA_VALUE': 'm2'}
        )
