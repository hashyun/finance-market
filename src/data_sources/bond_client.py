"""
한국 국채 수익률 클라이언트
국채 수익률 곡선 데이터 조회
"""
from typing import Dict, Optional
import pandas as pd
from datetime import datetime, timedelta
from pykrx import bond


class BondClient:
    """
    한국 국채 수익률 조회 클라이언트
    """

    def __init__(self):
        """
        국채 수익률 조회 초기화
        """
        pass

    def get_treasury_yields(
        self,
        start_date: Optional[str] = None,
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

        if start_date is None:
            # 기본적으로 최근 1년 데이터
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

        try:
            # pykrx를 사용한 국고채 수익률 조회
            df = bond.get_otc_treasury_yields(start_date, end_date)
            return df

        except Exception as e:
            print(f"국고채 수익률 조회 실패: {e}")
            return pd.DataFrame()

    def get_yield_curve(self, date: Optional[str] = None) -> Dict[str, float]:
        """
        특정일의 국채 수익률 곡선

        Args:
            date: 조회일 (YYYYMMDD), None이면 최근 영업일

        Returns:
            만기별 수익률 딕셔너리
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        try:
            df = self.get_treasury_yields(date, date)

            if df.empty:
                return {}

            # 최신 데이터 추출
            latest = df.iloc[-1]

            # 만기별 수익률 반환
            result = {}
            for col in df.columns:
                if '국고채' in col:
                    result[col] = float(latest[col]) if pd.notna(latest[col]) else None

            return result

        except Exception as e:
            print(f"수익률 곡선 조회 실패: {e}")
            return {}

    def calculate_spread(
        self,
        short_maturity: str = '국고채1년',
        long_maturity: str = '국고채10년',
        date: Optional[str] = None
    ) -> Optional[float]:
        """
        국채 스프레드 계산 (예: 10년 - 1년)

        Args:
            short_maturity: 단기 만기 (컬럼명)
            long_maturity: 장기 만기 (컬럼명)
            date: 조회일

        Returns:
            스프레드 (bp)
        """
        curve = self.get_yield_curve(date)

        if not curve or short_maturity not in curve or long_maturity not in curve:
            return None

        short_yield = curve[short_maturity]
        long_yield = curve[long_maturity]

        if short_yield is None or long_yield is None:
            return None

        # 스프레드 계산 (장기 - 단기)
        spread = long_yield - short_yield

        return spread

    def get_historical_spreads(
        self,
        short_maturity: str = '국고채1년',
        long_maturity: str = '국고채10년',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        국채 스프레드 시계열 조회

        Args:
            short_maturity: 단기 만기
            long_maturity: 장기 만기
            start_date: 시작일
            end_date: 종료일

        Returns:
            스프레드 시계열 데이터
        """
        df = self.get_treasury_yields(start_date, end_date)

        if df.empty:
            return pd.DataFrame()

        if short_maturity not in df.columns or long_maturity not in df.columns:
            print(f"경고: {short_maturity} 또는 {long_maturity} 데이터가 없습니다.")
            return pd.DataFrame()

        # 스프레드 계산
        df['spread'] = df[long_maturity] - df[short_maturity]

        return df[['spread']]

    def analyze_yield_curve_shape(self, date: Optional[str] = None) -> Dict[str, any]:
        """
        수익률 곡선 형태 분석

        Args:
            date: 조회일

        Returns:
            곡선 분석 결과
        """
        curve = self.get_yield_curve(date)

        if not curve:
            return {}

        # 주요 만기 추출
        try:
            y1 = curve.get('국고채1년')
            y3 = curve.get('국고채3년')
            y5 = curve.get('국고채5년')
            y10 = curve.get('국고채10년')
            y20 = curve.get('국고채20년')

            if None in [y1, y10]:
                return {}

            # 스프레드 분석
            spread_10_1 = y10 - y1 if y10 and y1 else None

            # 곡선 형태 판단
            shape = "정상"
            if spread_10_1 is not None:
                if spread_10_1 > 1.0:
                    shape = "가파른 우상향"
                elif spread_10_1 > 0:
                    shape = "완만한 우상향"
                elif spread_10_1 > -0.5:
                    shape = "평탄"
                else:
                    shape = "역전"

            return {
                'date': date,
                'shape': shape,
                'spread_10y_1y': spread_10_1,
                'yield_1y': y1,
                'yield_3y': y3,
                'yield_5y': y5,
                'yield_10y': y10,
                'yield_20y': y20,
            }

        except Exception as e:
            print(f"수익률 곡선 분석 실패: {e}")
            return {}

    def get_risk_free_rate(self, maturity: str = '3M') -> Optional[float]:
        """
        무위험 이자율 조회 (포트폴리오 최적화에 사용)

        Args:
            maturity: 만기 ('3M', '1Y', '3Y', '5Y', '10Y')

        Returns:
            무위험 이자율
        """
        maturity_map = {
            '3M': '국고채3개월',
            '1Y': '국고채1년',
            '3Y': '국고채3년',
            '5Y': '국고채5년',
            '10Y': '국고채10년'
        }

        curve = self.get_yield_curve()

        if not curve:
            # 기본값 반환
            return 0.035  # 3.5%

        col_name = maturity_map.get(maturity, '국고채3년')
        rate = curve.get(col_name)

        if rate is not None:
            # 백분율을 소수로 변환
            return rate / 100.0

        return 0.035  # 기본값
