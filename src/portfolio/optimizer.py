"""
포트폴리오 최적화 엔진
시장 위험, 신용 위험, 유동성 위험을 모두 고려한 스마트 포트폴리오 구성
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
from scipy.optimize import minimize
from ..models.stock import Stock, Portfolio
from ..risk.market_risk import MarketRiskAnalyzer
from ..risk.credit_risk import CreditRiskAnalyzer
from ..risk.liquidity_risk import LiquidityRiskAnalyzer


class PortfolioOptimizer:
    """
    포트폴리오 최적화 클래스
    """

    def __init__(
        self,
        stocks: List[Stock],
        risk_free_rate: float = 0.03,
        market_risk_weight: float = 0.4,
        credit_risk_weight: float = 0.3,
        liquidity_risk_weight: float = 0.3
    ):
        """
        Args:
            stocks: 투자 가능한 주식 리스트
            risk_free_rate: 무위험 수익률 (기본값 3%)
            market_risk_weight: 시장 위험 가중치
            credit_risk_weight: 신용 위험 가중치
            liquidity_risk_weight: 유동성 위험 가중치
        """
        self.stocks = stocks
        self.risk_free_rate = risk_free_rate
        self.market_risk_weight = market_risk_weight
        self.credit_risk_weight = credit_risk_weight
        self.liquidity_risk_weight = liquidity_risk_weight

        # 가중치 정규화
        total_weight = market_risk_weight + credit_risk_weight + liquidity_risk_weight
        self.market_risk_weight /= total_weight
        self.credit_risk_weight /= total_weight
        self.liquidity_risk_weight /= total_weight

    def calculate_composite_risk_score(self, portfolio: Portfolio) -> float:
        """
        종합 위험 점수 계산
        세 가지 위험을 통합하여 하나의 점수로 산출

        Args:
            portfolio: 포트폴리오 객체

        Returns:
            종합 위험 점수 (낮을수록 좋음)
        """
        # 1. 시장 위험: 변동성 기반 (높을수록 나쁨)
        volatility = portfolio.volatility()
        market_risk = volatility * 100  # 0~100 스케일로 변환

        # 2. 신용 위험: 신용 점수 기반 (100 - 점수 = 위험도)
        credit_score = CreditRiskAnalyzer.portfolio_credit_score(portfolio)
        credit_risk = 100 - credit_score

        # 3. 유동성 위험: 유동성 점수 기반 (100 - 점수 = 위험도)
        liquidity_score = LiquidityRiskAnalyzer.portfolio_liquidity_score(portfolio)
        liquidity_risk = 100 - liquidity_score

        # 가중 평균으로 종합 위험 점수 계산
        composite_risk = (
            self.market_risk_weight * market_risk +
            self.credit_risk_weight * credit_risk +
            self.liquidity_risk_weight * liquidity_risk
        )

        return composite_risk

    def risk_adjusted_return(self, portfolio: Portfolio) -> float:
        """
        위험 조정 수익률 계산
        수익률을 종합 위험으로 나눔

        Args:
            portfolio: 포트폴리오 객체

        Returns:
            위험 조정 수익률 (높을수록 좋음)
        """
        expected_return = portfolio.expected_return()
        composite_risk = self.calculate_composite_risk_score(portfolio)

        if composite_risk == 0:
            return float('inf')

        # 위험 조정 수익률 = 수익률 / 위험
        risk_adjusted = expected_return / (composite_risk / 100)

        return risk_adjusted

    def optimize_max_sharpe(self) -> Portfolio:
        """
        샤프 비율 최대화 포트폴리오 구성
        전통적인 포트폴리오 최적화 방법

        Returns:
            최적화된 포트폴리오
        """
        n_stocks = len(self.stocks)

        # 목적 함수: 샤프 비율의 음수 (최소화하기 위해)
        def objective(weights):
            portfolio = Portfolio(self.stocks, weights)
            return -portfolio.sharpe_ratio(self.risk_free_rate)

        # 제약조건
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}  # 비중 합 = 1
        ]

        # 경계조건: 각 비중은 0~1 사이
        bounds = [(0, 1) for _ in range(n_stocks)]

        # 초기값: 동일 비중
        initial_weights = np.array([1.0 / n_stocks] * n_stocks)

        # 최적화 실행
        result = minimize(
            objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        optimal_weights = result.x
        optimal_portfolio = Portfolio(self.stocks, optimal_weights)

        return optimal_portfolio

    def optimize_risk_aware(
        self,
        min_expected_return: Optional[float] = None,
        max_volatility: Optional[float] = None,
        min_credit_score: float = 30.0,
        min_liquidity_score: float = 30.0
    ) -> Portfolio:
        """
        위험 인식 포트폴리오 최적화
        시장 위험, 신용 위험, 유동성 위험을 모두 고려

        Args:
            min_expected_return: 최소 기대 수익률 제약
            max_volatility: 최대 변동성 제약
            min_credit_score: 최소 신용 점수 제약
            min_liquidity_score: 최소 유동성 점수 제약

        Returns:
            최적화된 포트폴리오
        """
        n_stocks = len(self.stocks)

        # 목적 함수: 종합 위험 점수 최소화 (수익률 고려)
        def objective(weights):
            portfolio = Portfolio(self.stocks, weights)
            # 위험을 최소화하면서 수익률을 최대화
            composite_risk = self.calculate_composite_risk_score(portfolio)
            expected_return = portfolio.expected_return()
            # 목적: 위험 최소화 - 수익률 최대화 (음수로 더함)
            return composite_risk - expected_return * 100

        # 제약조건 리스트
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}  # 비중 합 = 1
        ]

        # 최소 기대 수익률 제약
        if min_expected_return is not None:
            constraints.append({
                'type': 'ineq',
                'fun': lambda w: Portfolio(self.stocks, w).expected_return() - min_expected_return
            })

        # 최대 변동성 제약
        if max_volatility is not None:
            constraints.append({
                'type': 'ineq',
                'fun': lambda w: max_volatility - Portfolio(self.stocks, w).volatility()
            })

        # 최소 신용 점수 제약
        constraints.append({
            'type': 'ineq',
            'fun': lambda w: CreditRiskAnalyzer.portfolio_credit_score(
                Portfolio(self.stocks, w)
            ) - min_credit_score
        })

        # 최소 유동성 점수 제약
        constraints.append({
            'type': 'ineq',
            'fun': lambda w: LiquidityRiskAnalyzer.portfolio_liquidity_score(
                Portfolio(self.stocks, w)
            ) - min_liquidity_score
        })

        # 경계조건: 각 비중은 0~0.4 사이 (과도한 집중 방지)
        bounds = [(0, 0.4) for _ in range(n_stocks)]

        # 초기값: 동일 비중
        initial_weights = np.array([1.0 / n_stocks] * n_stocks)

        # 최적화 실행
        result = minimize(
            objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )

        if result.success:
            optimal_weights = result.x
        else:
            # 최적화 실패 시 동일 비중 반환
            print(f"최적화 실패: {result.message}")
            optimal_weights = initial_weights

        optimal_portfolio = Portfolio(self.stocks, optimal_weights)

        return optimal_portfolio

    def efficient_frontier(
        self,
        num_portfolios: int = 100
    ) -> List[Tuple[float, float, List[float]]]:
        """
        효율적 투자선 계산
        다양한 위험-수익률 조합의 포트폴리오 생성

        Args:
            num_portfolios: 생성할 포트폴리오 개수

        Returns:
            (수익률, 위험, 비중) 튜플의 리스트
        """
        n_stocks = len(self.stocks)
        results = []

        for _ in range(num_portfolios):
            # 랜덤 비중 생성
            weights = np.random.random(n_stocks)
            weights /= np.sum(weights)

            portfolio = Portfolio(self.stocks, weights)

            expected_return = portfolio.expected_return()
            risk = self.calculate_composite_risk_score(portfolio)

            results.append((expected_return, risk, weights.tolist()))

        # 수익률 기준으로 정렬
        results.sort(key=lambda x: x[0])

        return results

    def analyze_portfolio(self, portfolio: Portfolio) -> Dict:
        """
        포트폴리오 종합 분석
        모든 위험 지표와 성과 지표를 계산

        Args:
            portfolio: 분석할 포트폴리오

        Returns:
            분석 결과 딕셔너리
        """
        market_analyzer = MarketRiskAnalyzer()
        credit_analyzer = CreditRiskAnalyzer()
        liquidity_analyzer = LiquidityRiskAnalyzer()

        analysis = {
            # 기본 지표
            'expected_return': portfolio.expected_return(),
            'volatility': portfolio.volatility(),
            'sharpe_ratio': portfolio.sharpe_ratio(self.risk_free_rate),

            # 시장 위험
            'var_95': market_analyzer.value_at_risk(portfolio, 0.95),
            'cvar_95': market_analyzer.conditional_var(portfolio, 0.95),
            'max_drawdown': market_analyzer.maximum_drawdown(portfolio),
            'diversification_ratio': market_analyzer.diversification_ratio(portfolio),

            # 신용 위험
            'credit_score': credit_analyzer.portfolio_credit_score(portfolio),
            'concentration_risk': credit_analyzer.concentration_risk(portfolio),
            'sector_exposure': credit_analyzer.sector_exposure(portfolio),

            # 유동성 위험
            'liquidity_score': liquidity_analyzer.portfolio_liquidity_score(portfolio),
            'max_liquidation_days': liquidity_analyzer.portfolio_liquidation_time(
                portfolio, 100_000_000  # 1억원 기준
            ),

            # 종합 지표
            'composite_risk_score': self.calculate_composite_risk_score(portfolio),
            'risk_adjusted_return': self.risk_adjusted_return(portfolio),

            # 비중
            'weights': portfolio.get_weights_dict()
        }

        return analysis
