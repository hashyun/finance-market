"""
유동성 위험(Liquidity Risk) 분석 모듈
거래량, 시가총액, 매수-매도 스프레드 등을 분석
"""
import numpy as np
from typing import Dict
from ..models.stock import Stock, Portfolio


class LiquidityRiskAnalyzer:
    """
    유동성 위험 분석 클래스
    """

    @staticmethod
    def trading_volume_score(stock: Stock, market_avg_volume: float = 1000000) -> float:
        """
        거래량 점수 계산 (0~100)
        거래량이 많을수록 유동성이 좋음

        Args:
            stock: 주식 객체
            market_avg_volume: 시장 평균 거래량 (기준값)

        Returns:
            점수 (0~100)
        """
        # 시장 평균 대비 거래량 비율
        volume_ratio = stock.trading_volume / market_avg_volume

        if volume_ratio >= 2.0:
            return 100
        elif volume_ratio >= 1.0:
            return 80 + (volume_ratio - 1.0) * 20
        elif volume_ratio >= 0.5:
            return 50 + (volume_ratio - 0.5) * 60
        elif volume_ratio >= 0.1:
            return 20 + (volume_ratio - 0.1) * 75
        else:
            return max(0, volume_ratio * 200)

    @staticmethod
    def market_cap_score(stock: Stock, large_cap_threshold: float = 10_000_000_000_000) -> float:
        """
        시가총액 점수 계산 (0~100)
        시가총액이 클수록 유동성이 좋음

        Args:
            stock: 주식 객체
            large_cap_threshold: 대형주 기준 (원화 기준, 10조원)

        Returns:
            점수 (0~100)
        """
        market_cap_ratio = stock.market_cap / large_cap_threshold

        if market_cap_ratio >= 1.0:
            # 대형주
            return 100
        elif market_cap_ratio >= 0.3:
            # 중형주
            return 70 + (market_cap_ratio - 0.3) * 42.86
        elif market_cap_ratio >= 0.05:
            # 소형주
            return 40 + (market_cap_ratio - 0.05) * 120
        else:
            # 초소형주
            return max(0, market_cap_ratio * 800)

    @staticmethod
    def turnover_ratio(stock: Stock) -> float:
        """
        회전율 계산
        거래량 / 발행주식수 (시가총액/주가로 근사)

        Args:
            stock: 주식 객체

        Returns:
            회전율
        """
        if stock.price <= 0:
            return 0

        # 발행주식수 근사값
        shares_outstanding = stock.market_cap / stock.price

        if shares_outstanding <= 0:
            return 0

        # 회전율 = 거래량 / 발행주식수
        turnover = stock.trading_volume / shares_outstanding

        return turnover

    @staticmethod
    def liquidity_score(stock: Stock) -> float:
        """
        종합 유동성 점수 계산
        거래량과 시가총액을 종합하여 점수화

        Args:
            stock: 주식 객체

        Returns:
            종합 유동성 점수 (0~100)
        """
        # 거래량 점수 (60% 가중치)
        volume_score = LiquidityRiskAnalyzer.trading_volume_score(stock)

        # 시가총액 점수 (40% 가중치)
        cap_score = LiquidityRiskAnalyzer.market_cap_score(stock)

        # 가중 평균
        total_score = volume_score * 0.6 + cap_score * 0.4

        return total_score

    @staticmethod
    def portfolio_liquidity_score(portfolio: Portfolio) -> float:
        """
        포트폴리오 전체의 유동성 점수 계산
        각 종목의 유동성 점수를 비중으로 가중 평균

        Args:
            portfolio: 포트폴리오 객체

        Returns:
            포트폴리오 유동성 점수 (0~100)
        """
        scores = np.array([
            LiquidityRiskAnalyzer.liquidity_score(stock)
            for stock in portfolio.stocks
        ])

        portfolio_score = np.dot(portfolio.weights, scores)

        return portfolio_score

    @staticmethod
    def liquidity_adjusted_var(
        portfolio: Portfolio,
        var: float,
        liquidity_threshold: float = 50.0
    ) -> float:
        """
        유동성 조정 VaR
        유동성이 낮을수록 VaR이 증가

        Args:
            portfolio: 포트폴리오 객체
            var: 기존 VaR 값
            liquidity_threshold: 유동성 기준점 (50점 기준)

        Returns:
            유동성 조정 VaR
        """
        liquidity_score = LiquidityRiskAnalyzer.portfolio_liquidity_score(portfolio)

        # 유동성이 낮을수록 조정 계수가 증가
        if liquidity_score >= liquidity_threshold:
            adjustment_factor = 1.0
        else:
            # 유동성이 50점 미만이면 VaR 증가
            adjustment_factor = 1.0 + (liquidity_threshold - liquidity_score) / 100

        adjusted_var = var * adjustment_factor

        return adjusted_var

    @staticmethod
    def time_to_liquidate(stock: Stock, position_value: float) -> float:
        """
        청산 소요 시간 추정
        특정 금액의 포지션을 청산하는데 걸리는 시간 (일)

        Args:
            stock: 주식 객체
            position_value: 포지션 가치 (원)

        Returns:
            청산 소요 일수
        """
        # 일일 거래대금
        daily_trading_value = stock.trading_volume * stock.price

        if daily_trading_value <= 0:
            return float('inf')

        # 일일 거래대금의 10%만 영향 없이 거래 가능하다고 가정
        safe_daily_trading = daily_trading_value * 0.1

        # 청산 소요 일수
        days_to_liquidate = position_value / safe_daily_trading

        return days_to_liquidate

    @staticmethod
    def portfolio_liquidation_time(
        portfolio: Portfolio,
        total_portfolio_value: float
    ) -> float:
        """
        포트폴리오 전체 청산 소요 시간 추정

        Args:
            portfolio: 포트폴리오 객체
            total_portfolio_value: 포트폴리오 총 가치 (원)

        Returns:
            최대 청산 소요 일수
        """
        liquidation_times = []

        for stock, weight in zip(portfolio.stocks, portfolio.weights):
            position_value = total_portfolio_value * weight
            time = LiquidityRiskAnalyzer.time_to_liquidate(stock, position_value)
            liquidation_times.append(time)

        # 가장 오래 걸리는 종목 기준
        max_liquidation_time = max(liquidation_times)

        return max_liquidation_time

    @staticmethod
    def evaluate_liquidity_risk(portfolio: Portfolio, portfolio_value: float = 100_000_000) -> Dict[str, float]:
        """
        포트폴리오의 유동성 위험 종합 평가

        Args:
            portfolio: 포트폴리오 객체
            portfolio_value: 포트폴리오 가치 (원, 기본값 1억원)

        Returns:
            유동성 위험 지표들을 담은 딕셔너리
        """
        return {
            'portfolio_liquidity_score': LiquidityRiskAnalyzer.portfolio_liquidity_score(portfolio),
            'avg_trading_volume': np.dot(
                portfolio.weights,
                [stock.trading_volume for stock in portfolio.stocks]
            ),
            'avg_market_cap': np.dot(
                portfolio.weights,
                [stock.market_cap for stock in portfolio.stocks]
            ),
            'max_liquidation_days': LiquidityRiskAnalyzer.portfolio_liquidation_time(
                portfolio, portfolio_value
            ),
            'individual_liquidity_scores': {
                stock.ticker: LiquidityRiskAnalyzer.liquidity_score(stock)
                for stock in portfolio.stocks
            }
        }
