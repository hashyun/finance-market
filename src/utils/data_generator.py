"""
한국 시장 샘플 데이터 생성기
"""
import numpy as np
from datetime import datetime, timedelta
from typing import List
from ..models.korean_stock import KoreanStock, TradingData


class KoreanDataGenerator:
    """
    한국 주식 시장 샘플 데이터 생성
    """

    @staticmethod
    def generate_trading_data(
        start_price: float,
        num_days: int,
        volatility: float = 0.02,
        trend: float = 0.0005,
        foreign_bias: float = 0.0,  # 외국인 매수 편향
        start_date: str = "2024-01-01"
    ) -> List[TradingData]:
        """
        거래 데이터 생성

        Args:
            start_price: 시작 가격
            num_days: 생성할 일수
            volatility: 변동성
            trend: 추세 (양수: 상승, 음수: 하락)
            foreign_bias: 외국인 매수 편향 (-1 ~ 1)
            start_date: 시작 날짜

        Returns:
            TradingData 리스트
        """
        trading_data = []
        current_price = start_price
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")

        for i in range(num_days):
            # 날짜
            current_date = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")

            # 가격 변동
            daily_return = np.random.normal(trend, volatility)
            current_price = current_price * (1 + daily_return)

            # OHLC
            high = current_price * (1 + abs(np.random.normal(0, volatility/2)))
            low = current_price * (1 - abs(np.random.normal(0, volatility/2)))
            open_price = current_price * (1 + np.random.normal(0, volatility/3))
            close = current_price

            # 거래량
            base_volume = int(np.random.uniform(500_000, 2_000_000))
            volume = int(base_volume * (1 + abs(daily_return) * 10))

            # 외국인 매매
            foreign_net_ratio = foreign_bias + np.random.normal(0, 0.05)
            foreign_net = int(volume * foreign_net_ratio)
            foreign_buy = max(0, foreign_net) + int(volume * 0.15)
            foreign_sell = foreign_buy - foreign_net

            # 기관 매매 (외국인과 약한 상관관계)
            institution_net_ratio = foreign_bias * 0.6 + np.random.normal(0, 0.04)
            institution_net = int(volume * institution_net_ratio)
            institution_buy = max(0, institution_net) + int(volume * 0.12)
            institution_sell = institution_buy - institution_net

            # 개인 매매 (외국인/기관의 반대)
            individual_net = -(foreign_net + institution_net)
            individual_buy = int(volume * 0.7) if individual_net > 0 else int(volume * 0.3)
            individual_sell = individual_buy - individual_net

            # 프로그램 매매
            program_ratio = np.random.normal(0, 0.03)
            program_net = int(volume * program_ratio)
            program_buy = max(0, program_net) + int(volume * 0.2)
            program_sell = program_buy - program_net

            # 공매도
            short_sell_volume = int(volume * np.random.uniform(0.02, 0.15))
            short_balance = int(base_volume * np.random.uniform(0.5, 2.0))

            # 신용잔고
            credit_balance = np.random.uniform(50, 500)

            trading_data.append(TradingData(
                date=current_date,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume,
                foreign_buy=foreign_buy,
                foreign_sell=foreign_sell,
                institution_buy=institution_buy,
                institution_sell=institution_sell,
                individual_buy=individual_buy,
                individual_sell=individual_sell,
                program_buy=program_buy,
                program_sell=program_sell,
                short_sell_volume=short_sell_volume,
                short_balance=short_balance,
                credit_balance=credit_balance
            ))

        return trading_data

    @staticmethod
    def generate_sample_stocks(num_days: int = 100, start_date: str = "2024-01-01") -> List[KoreanStock]:
        """
        샘플 주식 데이터 생성

        Returns:
            KoreanStock 리스트
        """
        stocks = []

        # 삼성전자 - 외국인 선호 대형주
        stocks.append(KoreanStock(
            ticker="005930",
            name="삼성전자",
            sector="IT/전자",
            market="KOSPI",
            trading_data=KoreanDataGenerator.generate_trading_data(
                start_price=70000,
                num_days=num_days,
                volatility=0.018,
                trend=0.0003,
                foreign_bias=0.15,  # 외국인 매수 우세
                start_date=start_date
            ),
            market_cap=420_000_000_000_000,
            debt_to_equity=0.35,
            current_ratio=2.1,
            credit_rating="AA"
        ))

        # SK하이닉스 - 변동성 큰 반도체
        stocks.append(KoreanStock(
            ticker="000660",
            name="SK하이닉스",
            sector="IT/전자",
            market="KOSPI",
            trading_data=KoreanDataGenerator.generate_trading_data(
                start_price=130000,
                num_days=num_days,
                volatility=0.028,
                trend=0.0005,
                foreign_bias=0.10,
                start_date=start_date
            ),
            market_cap=95_000_000_000_000,
            debt_to_equity=0.45,
            current_ratio=1.8,
            credit_rating="A+"
        ))

        # NAVER - IT 성장주
        stocks.append(KoreanStock(
            ticker="035420",
            name="NAVER",
            sector="IT/인터넷",
            market="KOSPI",
            trading_data=KoreanDataGenerator.generate_trading_data(
                start_price=220000,
                num_days=num_days,
                volatility=0.022,
                trend=0.0004,
                foreign_bias=0.08,
                start_date=start_date
            ),
            market_cap=36_000_000_000_000,
            debt_to_equity=0.15,
            current_ratio=3.5,
            credit_rating="AA-"
        ))

        # 카카오 - 변동성 있는 성장주
        stocks.append(KoreanStock(
            ticker="035720",
            name="카카오",
            sector="IT/인터넷",
            market="KOSPI",
            trading_data=KoreanDataGenerator.generate_trading_data(
                start_price=50000,
                num_days=num_days,
                volatility=0.032,
                trend=0.0002,
                foreign_bias=-0.05,  # 개인 투자자 선호
                start_date=start_date
            ),
            market_cap=22_000_000_000_000,
            debt_to_equity=0.25,
            current_ratio=2.8,
            credit_rating="A"
        ))

        # 셀트리온 - 바이오 고변동성
        stocks.append(KoreanStock(
            ticker="068270",
            name="셀트리온",
            sector="바이오/제약",
            market="KOSPI",
            trading_data=KoreanDataGenerator.generate_trading_data(
                start_price=170000,
                num_days=num_days,
                volatility=0.045,
                trend=-0.0001,
                foreign_bias=0.12,
                start_date=start_date
            ),
            market_cap=23_000_000_000_000,
            debt_to_equity=0.2,
            current_ratio=4.2,
            credit_rating="A-"
        ))

        return stocks
