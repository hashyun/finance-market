"""
외국인/기관/개인 매매 동향 분석 모듈
"""
import numpy as np
from typing import Dict, List, Tuple
from ..models.korean_stock import KoreanStock, TradingData


class InvestorFlowAnalyzer:
    """
    투자자별 수급 분석 클래스
    """

    @staticmethod
    def foreign_strength(stock: KoreanStock, window: int = 20) -> float:
        """
        외국인 매수 강도 계산

        Args:
            stock: 한국 주식 객체
            window: 분석 기간 (일)

        Returns:
            외국인 매수 강도 (-100 ~ 100)
        """
        if len(stock.trading_data) < window:
            return 0.0

        recent_data = stock.trading_data[-window:]

        # 순매수 금액 (주식수 * 평균가격)
        foreign_net_sum = sum(td.foreign_net for td in recent_data)
        total_volume_sum = sum(td.volume for td in recent_data)

        if total_volume_sum == 0:
            return 0.0

        # 매수 강도: 순매수 / 총거래량 * 100
        strength = (foreign_net_sum / total_volume_sum) * 100

        return np.clip(strength, -100, 100)

    @staticmethod
    def institution_strength(stock: KoreanStock, window: int = 20) -> float:
        """
        기관 매수 강도 계산

        Returns:
            기관 매수 강도 (-100 ~ 100)
        """
        if len(stock.trading_data) < window:
            return 0.0

        recent_data = stock.trading_data[-window:]

        institution_net_sum = sum(td.institution_net for td in recent_data)
        total_volume_sum = sum(td.volume for td in recent_data)

        if total_volume_sum == 0:
            return 0.0

        strength = (institution_net_sum / total_volume_sum) * 100

        return np.clip(strength, -100, 100)

    @staticmethod
    def individual_strength(stock: KoreanStock, window: int = 20) -> float:
        """
        개인 매수 강도 계산

        Returns:
            개인 매수 강도 (-100 ~ 100)
        """
        if len(stock.trading_data) < window:
            return 0.0

        recent_data = stock.trading_data[-window:]

        individual_net_sum = sum(td.individual_net for td in recent_data)
        total_volume_sum = sum(td.volume for td in recent_data)

        if total_volume_sum == 0:
            return 0.0

        strength = (individual_net_sum / total_volume_sum) * 100

        return np.clip(strength, -100, 100)

    @staticmethod
    def investor_consensus(stock: KoreanStock, window: int = 20) -> Dict[str, float]:
        """
        투자자별 컨센서스 분석
        외국인과 기관이 동시에 매수하면 강한 신호

        Returns:
            각 투자자 그룹의 매수 강도와 컨센서스 점수
        """
        foreign = InvestorFlowAnalyzer.foreign_strength(stock, window)
        institution = InvestorFlowAnalyzer.institution_strength(stock, window)
        individual = InvestorFlowAnalyzer.individual_strength(stock, window)

        # 컨센서스 점수: 외국인과 기관이 같은 방향이면 높은 점수
        if foreign > 0 and institution > 0:
            consensus = (foreign + institution) / 2  # 둘 다 매수
        elif foreign < 0 and institution < 0:
            consensus = (foreign + institution) / 2  # 둘 다 매도
        else:
            consensus = 0  # 의견 불일치

        return {
            'foreign_strength': foreign,
            'institution_strength': institution,
            'individual_strength': individual,
            'consensus_score': consensus
        }

    @staticmethod
    def foreign_flow_trend(stock: KoreanStock, short_window: int = 5, long_window: int = 20) -> str:
        """
        외국인 수급 추세 분석
        단기/장기 이동평균을 비교하여 추세 판단

        Returns:
            "강한 매수", "매수", "중립", "매도", "강한 매도"
        """
        if len(stock.trading_data) < long_window:
            return "중립"

        # 단기 이동평균
        short_data = stock.trading_data[-short_window:]
        short_avg = np.mean([td.foreign_net for td in short_data])

        # 장기 이동평균
        long_data = stock.trading_data[-long_window:]
        long_avg = np.mean([td.foreign_net for td in long_data])

        # 추세 판단
        if short_avg > long_avg * 1.5:
            return "강한 매수"
        elif short_avg > long_avg:
            return "매수"
        elif short_avg < long_avg * -1.5:
            return "강한 매도"
        elif short_avg < long_avg:
            return "매도"
        else:
            return "중립"

    @staticmethod
    def program_trading_signal(stock: KoreanStock, window: int = 10) -> float:
        """
        프로그램 매매 신호
        프로그램 순매수가 증가하면 단기 모멘텀 발생

        Returns:
            프로그램 매매 신호 강도 (-100 ~ 100)
        """
        if len(stock.trading_data) < window:
            return 0.0

        recent_data = stock.trading_data[-window:]

        program_net_sum = sum(td.program_net for td in recent_data)
        total_volume_sum = sum(td.volume for td in recent_data)

        if total_volume_sum == 0:
            return 0.0

        signal = (program_net_sum / total_volume_sum) * 100

        return np.clip(signal, -100, 100)

    @staticmethod
    def short_squeeze_potential(stock: KoreanStock, window: int = 20) -> float:
        """
        공매도 숏 스퀴즈 가능성 분석
        공매도 비율이 높고 외국인/기관이 매수하면 숏 커버 가능

        Returns:
            숏 스퀴즈 가능성 점수 (0 ~ 100)
        """
        if len(stock.trading_data) < window:
            return 0.0

        recent_data = stock.trading_data[-window:]

        # 평균 공매도 비율
        short_ratios = [
            td.short_sell_volume / td.volume if td.volume > 0 else 0
            for td in recent_data
        ]
        avg_short_ratio = np.mean(short_ratios)

        # 외국인 + 기관 순매수
        foreign_inst_net = sum(
            td.foreign_net + td.institution_net
            for td in recent_data
        )

        # 공매도 비율이 높고 (10% 이상) 기관/외국인이 순매수하면 높은 점수
        if avg_short_ratio > 0.1 and foreign_inst_net > 0:
            # 공매도 비율 * 순매수 강도
            total_volume = sum(td.volume for td in recent_data)
            net_strength = foreign_inst_net / total_volume if total_volume > 0 else 0

            score = min(avg_short_ratio * 1000 * net_strength, 100)
            return score

        return 0.0

    @staticmethod
    def analyze_investor_flow(stock: KoreanStock) -> Dict:
        """
        투자자 수급 종합 분석

        Returns:
            수급 분석 결과 딕셔너리
        """
        consensus = InvestorFlowAnalyzer.investor_consensus(stock)
        trend = InvestorFlowAnalyzer.foreign_flow_trend(stock)
        program_signal = InvestorFlowAnalyzer.program_trading_signal(stock)
        squeeze_potential = InvestorFlowAnalyzer.short_squeeze_potential(stock)

        # 종합 점수 계산
        total_score = (
            consensus['consensus_score'] * 0.4 +  # 컨센서스 40%
            program_signal * 0.2 +  # 프로그램 매매 20%
            squeeze_potential * 0.4  # 숏 스퀴즈 가능성 40%
        )

        return {
            'foreign_strength': consensus['foreign_strength'],
            'institution_strength': consensus['institution_strength'],
            'individual_strength': consensus['individual_strength'],
            'consensus_score': consensus['consensus_score'],
            'foreign_trend': trend,
            'program_signal': program_signal,
            'short_squeeze_potential': squeeze_potential,
            'total_score': total_score
        }

    @staticmethod
    def find_foreign_favorites(stocks: List[KoreanStock], top_n: int = 10) -> List[Tuple[KoreanStock, float]]:
        """
        외국인이 선호하는 종목 찾기

        Args:
            stocks: 분석할 주식 리스트
            top_n: 상위 N개 종목

        Returns:
            (주식, 외국인 매수 강도) 튜플 리스트
        """
        stock_scores = []

        for stock in stocks:
            strength = InvestorFlowAnalyzer.foreign_strength(stock)
            stock_scores.append((stock, strength))

        # 매수 강도 기준 정렬
        stock_scores.sort(key=lambda x: x[1], reverse=True)

        return stock_scores[:top_n]

    @staticmethod
    def find_institution_favorites(stocks: List[KoreanStock], top_n: int = 10) -> List[Tuple[KoreanStock, float]]:
        """
        기관이 선호하는 종목 찾기
        """
        stock_scores = []

        for stock in stocks:
            strength = InvestorFlowAnalyzer.institution_strength(stock)
            stock_scores.append((stock, strength))

        stock_scores.sort(key=lambda x: x[1], reverse=True)

        return stock_scores[:top_n]
