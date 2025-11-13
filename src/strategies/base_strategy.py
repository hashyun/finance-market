"""
트레이딩 전략 베이스 클래스
"""
from abc import ABC, abstractmethod
from typing import Dict, List
from ..models.korean_stock import KoreanStock


class TradingSignal:
    """트레이딩 신호"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class BaseStrategy(ABC):
    """
    트레이딩 전략 추상 클래스
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_signal(self, stock: KoreanStock) -> str:
        """
        매매 신호 생성

        Args:
            stock: 한국 주식 객체

        Returns:
            "BUY", "SELL", "HOLD"
        """
        pass

    @abstractmethod
    def calculate_score(self, stock: KoreanStock) -> float:
        """
        종목 점수 계산 (-100 ~ 100)

        Returns:
            점수 (양수: 매수, 음수: 매도, 0: 중립)
        """
        pass

    def rank_stocks(self, stocks: List[KoreanStock], top_n: int = 5) -> List[tuple]:
        """
        종목 순위 매기기

        Args:
            stocks: 주식 리스트
            top_n: 상위 N개

        Returns:
            (주식, 점수) 튜플 리스트
        """
        stock_scores = []

        for stock in stocks:
            try:
                score = self.calculate_score(stock)
                stock_scores.append((stock, score))
            except Exception as e:
                # 오류 발생 시 해당 종목 스킵
                continue

        # 점수 기준 내림차순 정렬
        stock_scores.sort(key=lambda x: x[1], reverse=True)

        return stock_scores[:top_n]

    def __repr__(self) -> str:
        return f"{self.name} Strategy"
