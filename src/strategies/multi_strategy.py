"""
멀티 전략
여러 전략을 결합하여 사용
"""
from typing import List, Dict
from .base_strategy import BaseStrategy, TradingSignal
from ..models.korean_stock import KoreanStock


class MultiStrategy(BaseStrategy):
    """
    멀티 전략 - 여러 전략을 조합
    """

    def __init__(
        self,
        strategies: List[BaseStrategy],
        weights: List[float] = None
    ):
        """
        Args:
            strategies: 사용할 전략 리스트
            weights: 각 전략의 가중치 (None이면 동일 가중)
        """
        super().__init__("멀티 전략")
        self.strategies = strategies

        if weights is None:
            self.weights = [1.0 / len(strategies)] * len(strategies)
        else:
            # 가중치 정규화
            total = sum(weights)
            self.weights = [w / total for w in weights]

    def generate_signal(self, stock: KoreanStock) -> str:
        """매매 신호 생성"""
        score = self.calculate_score(stock)

        if score >= 40:
            return TradingSignal.BUY
        elif score <= -40:
            return TradingSignal.SELL
        else:
            return TradingSignal.HOLD

    def calculate_score(self, stock: KoreanStock) -> float:
        """
        종합 점수 계산

        Returns:
            -100 ~ 100
        """
        total_score = 0

        for strategy, weight in zip(self.strategies, self.weights):
            try:
                score = strategy.calculate_score(stock)
                total_score += score * weight
            except Exception as e:
                # 오류 발생 시 해당 전략 스킵
                continue

        return total_score

    def get_strategy_breakdown(self, stock: KoreanStock) -> Dict[str, float]:
        """
        각 전략별 점수 분해

        Returns:
            전략명: 점수 딕셔너리
        """
        breakdown = {}

        for strategy, weight in zip(self.strategies, self.weights):
            try:
                score = strategy.calculate_score(stock)
                weighted_score = score * weight
                breakdown[strategy.name] = {
                    'score': score,
                    'weight': weight,
                    'weighted_score': weighted_score,
                    'signal': strategy.generate_signal(stock)
                }
            except Exception as e:
                breakdown[strategy.name] = {
                    'error': str(e)
                }

        return breakdown
