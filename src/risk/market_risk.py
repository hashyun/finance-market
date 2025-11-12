"""
시장 위험(Market Risk) 분석 모듈
VaR, CVaR, 베타, 상관관계 등을 계산
"""
import numpy as np
from typing import List
from scipy import stats
from ..models.stock import Stock, Portfolio


class MarketRiskAnalyzer:
    """
    시장 위험 분석 클래스
    """

    @staticmethod
    def value_at_risk(
        portfolio: Portfolio,
        confidence_level: float = 0.95,
        time_horizon: int = 1
    ) -> float:
        """
        VaR (Value at Risk) 계산 - 역사적 시뮬레이션 방법

        Args:
            portfolio: 포트폴리오 객체
            confidence_level: 신뢰수준 (기본값 95%)
            time_horizon: 시간 단위 (일 수)

        Returns:
            VaR 값 (손실액, 양수)
        """
        # 각 주식의 수익률을 비중으로 가중 평균하여 포트폴리오 수익률 계산
        returns_matrix = np.array([stock.historical_returns for stock in portfolio.stocks])
        portfolio_returns = np.dot(portfolio.weights, returns_matrix)

        # 시간 단위 조정
        portfolio_returns = portfolio_returns * np.sqrt(time_horizon)

        # VaR 계산 (하위 (1-신뢰수준) 백분위수)
        var = -np.percentile(portfolio_returns, (1 - confidence_level) * 100)

        return var

    @staticmethod
    def conditional_var(
        portfolio: Portfolio,
        confidence_level: float = 0.95,
        time_horizon: int = 1
    ) -> float:
        """
        CVaR (Conditional Value at Risk) 또는 Expected Shortfall 계산
        VaR을 초과하는 손실의 평균

        Args:
            portfolio: 포트폴리오 객체
            confidence_level: 신뢰수준
            time_horizon: 시간 단위

        Returns:
            CVaR 값 (손실액, 양수)
        """
        returns_matrix = np.array([stock.historical_returns for stock in portfolio.stocks])
        portfolio_returns = np.dot(portfolio.weights, returns_matrix)
        portfolio_returns = portfolio_returns * np.sqrt(time_horizon)

        # VaR 계산
        var_threshold = -np.percentile(portfolio_returns, (1 - confidence_level) * 100)

        # VaR을 초과하는 손실의 평균
        losses = -portfolio_returns
        cvar = np.mean(losses[losses >= var_threshold])

        return cvar

    @staticmethod
    def calculate_beta(stock: Stock, market_returns: List[float]) -> float:
        """
        개별 주식의 베타(β) 계산
        베타는 시장 대비 주식의 민감도를 나타냄

        Args:
            stock: 주식 객체
            market_returns: 시장 수익률 데이터

        Returns:
            베타 값
        """
        market_returns_array = np.array(market_returns)

        # 공분산 / 시장 분산
        covariance = np.cov(stock.historical_returns, market_returns_array)[0, 1]
        market_variance = np.var(market_returns_array)

        beta = covariance / market_variance if market_variance != 0 else 1.0

        return beta

    @staticmethod
    def correlation_matrix(stocks: List[Stock]) -> np.ndarray:
        """
        주식 간 상관관계 행렬 계산

        Args:
            stocks: 주식 리스트

        Returns:
            상관관계 행렬 (numpy array)
        """
        returns_matrix = np.array([stock.historical_returns for stock in stocks])
        correlation = np.corrcoef(returns_matrix)

        return correlation

    @staticmethod
    def diversification_ratio(portfolio: Portfolio) -> float:
        """
        분산투자 비율 계산
        포트폴리오가 얼마나 잘 분산되어 있는지 측정

        Args:
            portfolio: 포트폴리오 객체

        Returns:
            분산투자 비율 (1보다 크면 분산 효과 있음)
        """
        # 가중 평균 변동성
        weighted_volatility = sum(
            w * stock.volatility()
            for w, stock in zip(portfolio.weights, portfolio.stocks)
        )

        # 포트폴리오 변동성
        portfolio_volatility = portfolio.volatility()

        # 분산투자 비율
        if portfolio_volatility > 0:
            diversification = weighted_volatility / portfolio_volatility
        else:
            diversification = 1.0

        return diversification

    @staticmethod
    def maximum_drawdown(portfolio: Portfolio) -> float:
        """
        최대 낙폭(Maximum Drawdown) 계산

        Args:
            portfolio: 포트폴리오 객체

        Returns:
            최대 낙폭 (백분율)
        """
        returns_matrix = np.array([stock.historical_returns for stock in portfolio.stocks])
        portfolio_returns = np.dot(portfolio.weights, returns_matrix)

        # 누적 수익률
        cumulative_returns = np.cumprod(1 + portfolio_returns)

        # 최대값 대비 하락폭
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max

        max_drawdown = np.min(drawdown)

        return abs(max_drawdown)
