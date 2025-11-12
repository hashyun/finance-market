"""
신용 위험(Credit Risk) 분석 모듈
기업의 재무 건전성, 부채비율, 신용등급 등을 분석
"""
import numpy as np
from typing import Dict, List
from ..models.stock import Stock, Portfolio


class CreditRiskAnalyzer:
    """
    신용 위험 분석 클래스
    """

    # 신용등급별 점수 (높을수록 좋음)
    CREDIT_RATING_SCORES = {
        'AAA': 100,
        'AA+': 95,
        'AA': 90,
        'AA-': 85,
        'A+': 80,
        'A': 75,
        'A-': 70,
        'BBB+': 65,
        'BBB': 60,
        'BBB-': 55,
        'BB+': 50,
        'BB': 45,
        'BB-': 40,
        'B+': 35,
        'B': 30,
        'B-': 25,
        'CCC': 20,
        'CC': 10,
        'C': 5,
        'D': 0,
        None: 50  # 등급 없으면 중간값
    }

    @staticmethod
    def debt_to_equity_score(debt_to_equity: float) -> float:
        """
        부채비율 점수 계산 (0~100)
        부채비율이 낮을수록 높은 점수

        Args:
            debt_to_equity: 부채비율 (부채/자기자본)

        Returns:
            점수 (0~100)
        """
        if debt_to_equity <= 0.5:
            return 100
        elif debt_to_equity <= 1.0:
            return 90 - (debt_to_equity - 0.5) * 40
        elif debt_to_equity <= 2.0:
            return 70 - (debt_to_equity - 1.0) * 40
        elif debt_to_equity <= 3.0:
            return 30 - (debt_to_equity - 2.0) * 20
        else:
            return max(0, 10 - (debt_to_equity - 3.0) * 5)

    @staticmethod
    def current_ratio_score(current_ratio: float) -> float:
        """
        유동비율 점수 계산 (0~100)
        유동비율이 높을수록 단기 부채 상환 능력이 좋음

        Args:
            current_ratio: 유동비율 (유동자산/유동부채)

        Returns:
            점수 (0~100)
        """
        if current_ratio >= 2.0:
            return 100
        elif current_ratio >= 1.5:
            return 80 + (current_ratio - 1.5) * 40
        elif current_ratio >= 1.0:
            return 50 + (current_ratio - 1.0) * 60
        elif current_ratio >= 0.5:
            return 20 + (current_ratio - 0.5) * 60
        else:
            return max(0, current_ratio * 40)

    @staticmethod
    def credit_score(stock: Stock) -> float:
        """
        종합 신용 점수 계산
        신용등급, 부채비율, 유동비율을 종합하여 점수화

        Args:
            stock: 주식 객체

        Returns:
            종합 신용 점수 (0~100)
        """
        # 신용등급 점수 (40% 가중치)
        rating_score = CreditRiskAnalyzer.CREDIT_RATING_SCORES.get(stock.credit_rating, 50)

        # 부채비율 점수 (30% 가중치)
        debt_score = CreditRiskAnalyzer.debt_to_equity_score(stock.debt_to_equity)

        # 유동비율 점수 (30% 가중치)
        liquidity_score = CreditRiskAnalyzer.current_ratio_score(stock.current_ratio)

        # 가중 평균
        total_score = (
            rating_score * 0.4 +
            debt_score * 0.3 +
            liquidity_score * 0.3
        )

        return total_score

    @staticmethod
    def portfolio_credit_score(portfolio: Portfolio) -> float:
        """
        포트폴리오 전체의 신용 점수 계산
        각 종목의 신용 점수를 비중으로 가중 평균

        Args:
            portfolio: 포트폴리오 객체

        Returns:
            포트폴리오 신용 점수 (0~100)
        """
        scores = np.array([
            CreditRiskAnalyzer.credit_score(stock)
            for stock in portfolio.stocks
        ])

        portfolio_score = np.dot(portfolio.weights, scores)

        return portfolio_score

    @staticmethod
    def default_probability(stock: Stock) -> float:
        """
        부도 확률 추정 (단순화된 모델)
        신용 점수를 기반으로 부도 확률을 추정

        Args:
            stock: 주식 객체

        Returns:
            부도 확률 (0~1)
        """
        credit_score = CreditRiskAnalyzer.credit_score(stock)

        # 로지스틱 함수를 사용하여 점수를 확률로 변환
        # 점수가 높으면 부도 확률이 낮음
        default_prob = 1 / (1 + np.exp((credit_score - 50) / 10))

        return default_prob

    @staticmethod
    def concentration_risk(portfolio: Portfolio) -> float:
        """
        집중 위험 측정
        특정 종목이나 섹터에 과도하게 집중되었는지 확인

        Args:
            portfolio: 포트폴리오 객체

        Returns:
            집중 위험 지수 (0~1, 높을수록 집중됨)
        """
        # Herfindahl-Hirschman Index (HHI) 사용
        hhi = np.sum(portfolio.weights ** 2)

        return hhi

    @staticmethod
    def sector_exposure(portfolio: Portfolio) -> Dict[str, float]:
        """
        섹터별 노출도 계산

        Args:
            portfolio: 포트폴리오 객체

        Returns:
            섹터별 비중 딕셔너리
        """
        sector_weights = {}

        for stock, weight in zip(portfolio.stocks, portfolio.weights):
            if stock.sector in sector_weights:
                sector_weights[stock.sector] += weight
            else:
                sector_weights[stock.sector] = weight

        return sector_weights

    @staticmethod
    def evaluate_credit_risk(portfolio: Portfolio) -> Dict[str, float]:
        """
        포트폴리오의 신용 위험 종합 평가

        Args:
            portfolio: 포트폴리오 객체

        Returns:
            신용 위험 지표들을 담은 딕셔너리
        """
        return {
            'portfolio_credit_score': CreditRiskAnalyzer.portfolio_credit_score(portfolio),
            'concentration_risk': CreditRiskAnalyzer.concentration_risk(portfolio),
            'avg_debt_to_equity': np.dot(
                portfolio.weights,
                [stock.debt_to_equity for stock in portfolio.stocks]
            ),
            'avg_current_ratio': np.dot(
                portfolio.weights,
                [stock.current_ratio for stock in portfolio.stocks]
            ),
            'sector_exposure': CreditRiskAnalyzer.sector_exposure(portfolio)
        }
