"""
한국 시장 특화 주식 데이터 모델
외국인/기관/개인 매매, 공매도, 프로그램 매매 등 포함
"""
from typing import List, Dict, Optional
import numpy as np
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TradingData:
    """
    일별 거래 데이터
    """
    date: str  # 날짜 (YYYY-MM-DD)
    open: float  # 시가
    high: float  # 고가
    low: float  # 저가
    close: float  # 종가
    volume: int  # 거래량

    # 한국 시장 특화 데이터
    foreign_buy: int = 0  # 외국인 매수량
    foreign_sell: int = 0  # 외국인 매도량
    institution_buy: int = 0  # 기관 매수량
    institution_sell: int = 0  # 기관 매도량
    individual_buy: int = 0  # 개인 매수량
    individual_sell: int = 0  # 개인 매도량

    program_buy: int = 0  # 프로그램 매수량
    program_sell: int = 0  # 프로그램 매도량

    short_sell_volume: int = 0  # 공매도 거래량
    short_balance: int = 0  # 공매도 잔고

    credit_balance: float = 0  # 신용잔고 (억원)

    @property
    def foreign_net(self) -> int:
        """외국인 순매수"""
        return self.foreign_buy - self.foreign_sell

    @property
    def institution_net(self) -> int:
        """기관 순매수"""
        return self.institution_buy - self.institution_sell

    @property
    def individual_net(self) -> int:
        """개인 순매수"""
        return self.individual_buy - self.individual_sell

    @property
    def program_net(self) -> int:
        """프로그램 순매수"""
        return self.program_buy - self.program_sell

    @property
    def returns(self) -> float:
        """일일 수익률 (전일 종가 필요)"""
        # 이 메서드는 KoreanStock 클래스에서 계산됨
        return 0.0


class KoreanStock:
    """
    한국 시장 주식 클래스
    """

    def __init__(
        self,
        ticker: str,
        name: str,
        sector: str,
        market: str,  # "KOSPI" or "KOSDAQ"
        trading_data: List[TradingData],
        # 기존 Stock 클래스와의 호환성
        market_cap: float = 0,
        debt_to_equity: float = 0.0,
        current_ratio: float = 1.0,
        credit_rating: Optional[str] = None
    ):
        """
        Args:
            ticker: 종목 코드
            name: 종목명
            sector: 업종
            market: 시장 (KOSPI/KOSDAQ)
            trading_data: 일별 거래 데이터 리스트
            market_cap: 시가총액
            debt_to_equity: 부채비율
            current_ratio: 유동비율
            credit_rating: 신용등급
        """
        self.ticker = ticker
        self.name = name
        self.sector = sector
        self.market = market
        self.trading_data = sorted(trading_data, key=lambda x: x.date)
        self.market_cap = market_cap
        self.debt_to_equity = debt_to_equity
        self.current_ratio = current_ratio
        self.credit_rating = credit_rating

    @property
    def price(self) -> float:
        """현재가 (최근 종가)"""
        if self.trading_data:
            return self.trading_data[-1].close
        return 0.0

    @property
    def trading_volume(self) -> float:
        """평균 거래량"""
        if self.trading_data:
            volumes = [td.volume for td in self.trading_data]
            return np.mean(volumes)
        return 0.0

    def get_price_data(self) -> np.ndarray:
        """종가 데이터 배열"""
        return np.array([td.close for td in self.trading_data])

    def get_returns(self) -> np.ndarray:
        """수익률 데이터 배열"""
        prices = self.get_price_data()
        if len(prices) < 2:
            return np.array([])
        returns = (prices[1:] - prices[:-1]) / prices[:-1]
        return returns

    def get_foreign_net_flow(self, window: int = None) -> np.ndarray:
        """
        외국인 순매수 데이터

        Args:
            window: 이동평균 윈도우 (None이면 원본 데이터)
        """
        net_flow = np.array([td.foreign_net for td in self.trading_data])

        if window and window > 1:
            # 이동평균
            return np.convolve(net_flow, np.ones(window)/window, mode='valid')

        return net_flow

    def get_institution_net_flow(self, window: int = None) -> np.ndarray:
        """기관 순매수 데이터"""
        net_flow = np.array([td.institution_net for td in self.trading_data])

        if window and window > 1:
            return np.convolve(net_flow, np.ones(window)/window, mode='valid')

        return net_flow

    def get_program_net_flow(self, window: int = None) -> np.ndarray:
        """프로그램 순매수 데이터"""
        net_flow = np.array([td.program_net for td in self.trading_data])

        if window and window > 1:
            return np.convolve(net_flow, np.ones(window)/window, mode='valid')

        return net_flow

    def get_short_sell_ratio(self) -> np.ndarray:
        """공매도 비율 (공매도량 / 총거래량)"""
        ratios = []
        for td in self.trading_data:
            if td.volume > 0:
                ratios.append(td.short_sell_volume / td.volume)
            else:
                ratios.append(0.0)
        return np.array(ratios)

    def calculate_indicators(self) -> Dict[str, float]:
        """
        한국 시장 특화 지표 계산
        """
        if len(self.trading_data) < 20:
            return {}

        # 최근 20일 데이터
        recent_data = self.trading_data[-20:]

        # 외국인 순매수 누적
        foreign_net_20d = sum(td.foreign_net for td in recent_data)

        # 기관 순매수 누적
        institution_net_20d = sum(td.institution_net for td in recent_data)

        # 평균 공매도 비율
        short_ratios = [
            td.short_sell_volume / td.volume if td.volume > 0 else 0
            for td in recent_data
        ]
        avg_short_ratio = np.mean(short_ratios)

        # 최근 신용잔고
        recent_credit = recent_data[-1].credit_balance

        # 거래대금 회전율
        prices = [td.close for td in recent_data]
        volumes = [td.volume for td in recent_data]
        avg_turnover = np.mean(volumes) / (self.market_cap / np.mean(prices)) if self.market_cap > 0 else 0

        return {
            'foreign_net_20d': foreign_net_20d,
            'institution_net_20d': institution_net_20d,
            'avg_short_ratio_20d': avg_short_ratio,
            'credit_balance': recent_credit,
            'turnover_rate': avg_turnover
        }

    def __repr__(self) -> str:
        return f"KoreanStock({self.ticker}, {self.name}, {self.market})"


class KoreanPortfolio:
    """
    한국 시장 포트폴리오 클래스
    """

    def __init__(
        self,
        stocks: List[KoreanStock],
        weights: Optional[List[float]] = None,
        initial_capital: float = 100_000_000  # 초기 자본 (1억원)
    ):
        """
        Args:
            stocks: 포트폴리오에 포함된 주식 리스트
            weights: 각 주식의 비중
            initial_capital: 초기 투자 금액 (원)
        """
        self.stocks = stocks
        self.initial_capital = initial_capital

        if weights is None:
            self.weights = np.array([1.0 / len(stocks)] * len(stocks))
        else:
            self.weights = np.array(weights)
            self.weights = self.weights / np.sum(self.weights)

    def expected_return(self) -> float:
        """포트폴리오 기대 수익률"""
        returns_list = [stock.get_returns() for stock in self.stocks]
        if any(len(r) == 0 for r in returns_list):
            return 0.0

        expected_returns = np.array([np.mean(r) for r in returns_list])
        return np.dot(self.weights, expected_returns)

    def volatility(self) -> float:
        """포트폴리오 변동성"""
        returns_list = [stock.get_returns() for stock in self.stocks]

        if any(len(r) == 0 for r in returns_list):
            return 0.0

        # 모든 주식의 데이터 길이를 맞춤
        min_length = min(len(r) for r in returns_list)
        returns_matrix = np.array([r[-min_length:] for r in returns_list])

        cov_matrix = np.cov(returns_matrix)
        portfolio_variance = np.dot(self.weights, np.dot(cov_matrix, self.weights))

        return np.sqrt(portfolio_variance)

    def get_positions(self) -> Dict[str, Dict]:
        """
        포지션 정보 계산

        Returns:
            종목별 투자금액, 주식수 등
        """
        positions = {}

        for stock, weight in zip(self.stocks, self.weights):
            investment = self.initial_capital * weight
            shares = int(investment / stock.price)
            actual_investment = shares * stock.price

            positions[stock.ticker] = {
                'name': stock.name,
                'weight': weight,
                'target_investment': investment,
                'shares': shares,
                'actual_investment': actual_investment,
                'price': stock.price
            }

        return positions

    def __repr__(self) -> str:
        return f"KoreanPortfolio({len(self.stocks)} stocks, Capital: {self.initial_capital:,.0f}원)"
