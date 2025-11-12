"""
외국인 수급 추종 전략
외국인과 기관의 매수세가 강한 종목을 선택
"""
from .base_strategy import BaseStrategy, TradingSignal
from ..models.korean_stock import KoreanStock
from ..analysis.investor_flow import InvestorFlowAnalyzer


class ForeignFollowStrategy(BaseStrategy):
    """
    외국인 수급 추종 전략

    전략 로직:
    1. 외국인 + 기관 순매수가 양수 → 매수 신호
    2. 컨센서스 점수가 높을수록 강한 신호
    3. 프로그램 매매 신호도 고려
    """

    def __init__(
        self,
        buy_threshold: float = 30.0,
        sell_threshold: float = -30.0,
        consensus_weight: float = 0.6,
        program_weight: float = 0.4
    ):
        """
        Args:
            buy_threshold: 매수 임계값
            sell_threshold: 매도 임계값
            consensus_weight: 컨센서스 가중치
            program_weight: 프로그램 매매 가중치
        """
        super().__init__("외국인 수급 추종")
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.consensus_weight = consensus_weight
        self.program_weight = program_weight

    def generate_signal(self, stock: KoreanStock) -> str:
        """매매 신호 생성"""
        score = self.calculate_score(stock)

        if score >= self.buy_threshold:
            return TradingSignal.BUY
        elif score <= self.sell_threshold:
            return TradingSignal.SELL
        else:
            return TradingSignal.HOLD

    def calculate_score(self, stock: KoreanStock) -> float:
        """
        종목 점수 계산

        Returns:
            -100 ~ 100 (양수: 매수, 음수: 매도)
        """
        # 투자자 수급 분석
        flow_analysis = InvestorFlowAnalyzer.analyze_investor_flow(stock)

        # 컨센서스 점수 (외국인 + 기관 일치도)
        consensus_score = flow_analysis['consensus_score']

        # 프로그램 매매 신호
        program_signal = flow_analysis['program_signal']

        # 종합 점수
        total_score = (
            consensus_score * self.consensus_weight +
            program_signal * self.program_weight
        )

        return total_score
