"""
모멘텀 전략
가격 상승 추세가 강한 종목을 선택
"""
import numpy as np
from .base_strategy import BaseStrategy, TradingSignal
from ..models.korean_stock import KoreanStock
from ..analysis.market_indicators import KoreanMarketIndicators


class MomentumStrategy(BaseStrategy):
    """
    모멘텀 전략

    전략 로직:
    1. 이동평균선 정배열 (단기 > 장기) → 매수
    2. RSI가 과매수/과매도 구간 확인
    3. MACD 골든크로스/데드크로스
    4. 거래량 증가 확인
    """

    def __init__(
        self,
        rsi_buy_max: float = 70,  # RSI 매수 상한
        rsi_sell_min: float = 30,  # RSI 매도 하한
        ma_weight: float = 0.4,
        rsi_weight: float = 0.3,
        macd_weight: float = 0.3
    ):
        super().__init__("모멘텀")
        self.rsi_buy_max = rsi_buy_max
        self.rsi_sell_min = rsi_sell_min
        self.ma_weight = ma_weight
        self.rsi_weight = rsi_weight
        self.macd_weight = macd_weight

    def generate_signal(self, stock: KoreanStock) -> str:
        """매매 신호 생성"""
        score = self.calculate_score(stock)

        if score >= 50:
            return TradingSignal.BUY
        elif score <= -50:
            return TradingSignal.SELL
        else:
            return TradingSignal.HOLD

    def calculate_score(self, stock: KoreanStock) -> float:
        """
        모멘텀 점수 계산

        Returns:
            -100 ~ 100
        """
        indicators = KoreanMarketIndicators.calculate_all_indicators(stock)

        if not indicators:
            return 0.0

        # 1. 이동평균 점수
        ma_score = self._calculate_ma_score(indicators)

        # 2. RSI 점수
        rsi_score = self._calculate_rsi_score(indicators)

        # 3. MACD 점수
        macd_score = self._calculate_macd_score(indicators)

        # 종합 점수
        total_score = (
            ma_score * self.ma_weight +
            rsi_score * self.rsi_weight +
            macd_score * self.macd_weight
        )

        return total_score

    def _calculate_ma_score(self, indicators: dict) -> float:
        """이동평균 점수 (-100 ~ 100)"""
        price = indicators['price']
        ma5 = indicators['ma5']
        ma20 = indicators['ma20']
        ma60 = indicators['ma60']

        score = 0

        # 정배열 체크
        if ma5 > ma20 > ma60:
            score += 60  # 강한 상승 추세

        if price > ma5:
            score += 20
        if price > ma20:
            score += 20

        # 역배열 체크
        if ma5 < ma20 < ma60:
            score -= 60  # 강한 하락 추세

        if price < ma5:
            score -= 20
        if price < ma20:
            score -= 20

        return np.clip(score, -100, 100)

    def _calculate_rsi_score(self, indicators: dict) -> float:
        """RSI 점수 (-100 ~ 100)"""
        rsi = indicators['rsi']

        if rsi >= 70:
            # 과매수: 조정 가능성
            return -50
        elif rsi >= 50:
            # 강세 지속
            return 50
        elif rsi >= 30:
            # 약세 지속
            return -50
        else:
            # 과매도: 반등 가능성
            return 50

    def _calculate_macd_score(self, indicators: dict) -> float:
        """MACD 점수 (-100 ~ 100)"""
        macd = indicators['macd']
        signal = indicators['macd_signal']
        histogram = indicators['macd_histogram']

        score = 0

        # 골든크로스/데드크로스
        if macd > signal:
            score += 60  # 골든크로스
        else:
            score -= 60  # 데드크로스

        # 히스토그램 방향
        if histogram > 0:
            score += 40
        else:
            score -= 40

        return np.clip(score, -100, 100)
