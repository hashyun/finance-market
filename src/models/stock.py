"""
주식 및 포트폴리오 데이터 모델
"""
from typing import List, Dict, Optional
import numpy as np


class Stock:
    """
    개별 주식 정보를 담는 클래스
    """

    def __init__(
        self,
        ticker: str,
        name: str,
        sector: str,
        price: float,
        historical_returns: List[float],
        trading_volume: float,
        market_cap: float,
        debt_to_equity: float = 0.0,
        current_ratio: float = 1.0,
        credit_rating: Optional[str] = None
    ):
        """
        Args:
            ticker: 종목 코드
            name: 종목명
            sector: 업종
            price: 현재가
            historical_returns: 과거 수익률 데이터 (리스트)
            trading_volume: 일평균 거래량
            market_cap: 시가총액
            debt_to_equity: 부채비율 (신용 위험)
            current_ratio: 유동비율 (유동성 위험)
            credit_rating: 신용등급 (AAA, AA, A, BBB, BB, B, CCC 등)
        """
        self.ticker = ticker
        self.name = name
        self.sector = sector
        self.price = price
        self.historical_returns = np.array(historical_returns)
        self.trading_volume = trading_volume
        self.market_cap = market_cap
        self.debt_to_equity = debt_to_equity
        self.current_ratio = current_ratio
        self.credit_rating = credit_rating

    def expected_return(self) -> float:
        """기대 수익률 계산"""
        return np.mean(self.historical_returns)

    def volatility(self) -> float:
        """변동성 (표준편차) 계산"""
        return np.std(self.historical_returns)

    def __repr__(self) -> str:
        return f"Stock({self.ticker}, {self.name}, {self.sector})"


class Portfolio:
    """
    포트폴리오 클래스
    """

    def __init__(self, stocks: List[Stock], weights: Optional[List[float]] = None):
        """
        Args:
            stocks: 포트폴리오에 포함된 주식 리스트
            weights: 각 주식의 비중 (합이 1이어야 함)
        """
        self.stocks = stocks

        if weights is None:
            # 동일 비중으로 초기화
            self.weights = np.array([1.0 / len(stocks)] * len(stocks))
        else:
            self.weights = np.array(weights)
            # 비중의 합이 1이 되도록 정규화
            self.weights = self.weights / np.sum(self.weights)

    def expected_return(self) -> float:
        """포트폴리오 기대 수익률"""
        returns = np.array([stock.expected_return() for stock in self.stocks])
        return np.dot(self.weights, returns)

    def volatility(self) -> float:
        """포트폴리오 변동성"""
        returns_matrix = np.array([stock.historical_returns for stock in self.stocks])
        cov_matrix = np.cov(returns_matrix)
        portfolio_variance = np.dot(self.weights, np.dot(cov_matrix, self.weights))
        return np.sqrt(portfolio_variance)

    def sharpe_ratio(self, risk_free_rate: float = 0.03) -> float:
        """샤프 비율 계산"""
        excess_return = self.expected_return() - risk_free_rate
        return excess_return / self.volatility()

    def get_weights_dict(self) -> Dict[str, float]:
        """종목별 비중을 딕셔너리로 반환"""
        return {stock.ticker: weight for stock, weight in zip(self.stocks, self.weights)}

    def __repr__(self) -> str:
        return f"Portfolio({len(self.stocks)} stocks, Expected Return: {self.expected_return():.2%})"
