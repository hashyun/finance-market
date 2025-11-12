"""
평균회귀 전략
과매도 구간에서 매수, 과매수 구간에서 매도
"""
from .base_strategy import BaseStrategy, TradingSignal
from ..models.korean_stock import KoreanStock
from ..analysis.market_indicators import KoreanMarketIndicators


class MeanReversionStrategy(BaseStrategy):
    """
    평균회귀 전략

    전략 로직:
    1. 볼린저 밴드 하단 돌파 → 매수
    2. 볼린저 밴드 상단 돌파 → 매도
    3. 스토캐스틱이 과매도/과매수 구간 확인
    4. RSI가 극단적인 값일 때 반대 매매
    """

    def __init__(
        self,
        bb_lower_threshold: float = 20,  # 볼린저 밴드 하단 (%)
        bb_upper_threshold: float = 80,  # 볼린저 밴드 상단 (%)
        rsi_oversold: float = 30,
        rsi_overbought: float = 70,
        stoch_oversold: float = 20,
        stoch_overbought: float = 80
    ):
        super().__init__("평균회귀")
        self.bb_lower_threshold = bb_lower_threshold
        self.bb_upper_threshold = bb_upper_threshold
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.stoch_oversold = stoch_oversold
        self.stoch_overbought = stoch_overbought

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
        평균회귀 점수 계산

        Returns:
            -100 ~ 100 (양수: 매수, 음수: 매도)
        """
        indicators = KoreanMarketIndicators.calculate_all_indicators(stock)

        if not indicators:
            return 0.0

        score = 0

        # 1. 볼린저 밴드 점수
        bb_position = indicators['bb_position']

        if bb_position <= self.bb_lower_threshold:
            # 하단 근처 → 매수 신호 (반등 기대)
            score += 40
        elif bb_position >= self.bb_upper_threshold:
            # 상단 근처 → 매도 신호 (조정 기대)
            score -= 40

        # 2. RSI 점수
        rsi = indicators['rsi']

        if rsi <= self.rsi_oversold:
            # 과매도 → 매수
            score += 30
        elif rsi >= self.rsi_overbought:
            # 과매수 → 매도
            score -= 30

        # 3. 스토캐스틱 점수
        stoch_k = indicators['stochastic_k']
        stoch_d = indicators['stochastic_d']

        if stoch_k <= self.stoch_oversold and stoch_d <= self.stoch_oversold:
            # 과매도 → 매수
            score += 30
        elif stoch_k >= self.stoch_overbought and stoch_d >= self.stoch_overbought:
            # 과매수 → 매도
            score -= 30

        return score
