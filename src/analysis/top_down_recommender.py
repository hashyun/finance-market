"""
탑다운 관점에서 투자주체(외국인/기관/개인)별 한국 시장 해석과 종목 추천을 수행하는 모듈.
"""
from dataclasses import dataclass
from typing import Dict, List
import numpy as np

from .investor_flow import InvestorFlowAnalyzer
from ..models.korean_stock import KoreanStock


@dataclass
class MarketContext:
    """탑다운 시장 환경 입력값"""
    risk_on_score: float  # 0~100, 높을수록 위험자산 선호
    usdkrw_trend: str  # "up" | "down" | "flat"
    policy_rate_direction: str  # "up" | "down" | "hold"
    export_cycle_score: float  # 0~100, 한국 수출 사이클 강도


@dataclass
class ParticipantView:
    """투자주체별 한국시장 관점"""
    participant: str
    stance: str
    confidence: float
    logic: List[str]


@dataclass
class StockRecommendation:
    """종목 추천 결과"""
    ticker: str
    name: str
    total_score: float
    participant_scores: Dict[str, float]
    reasons: List[str]


class TopDownParticipantRecommender:
    """
    외국인/기관/개인의 성향을 반영한 탑다운 기반 종목 추천기.
    """

    @staticmethod
    def analyze_participant_views(context: MarketContext) -> Dict[str, ParticipantView]:
        foreign_bias = (
            context.export_cycle_score * 0.45
            + context.risk_on_score * 0.25
            + (100 if context.usdkrw_trend == "down" else 35 if context.usdkrw_trend == "flat" else 15) * 0.3
        )
        institution_bias = (
            context.risk_on_score * 0.3
            + context.export_cycle_score * 0.2
            + (80 if context.policy_rate_direction == "down" else 45 if context.policy_rate_direction == "hold" else 20) * 0.5
        )
        individual_bias = (
            context.risk_on_score * 0.6
            + (85 if context.policy_rate_direction == "down" else 55 if context.policy_rate_direction == "hold" else 40) * 0.2
            + (75 if context.usdkrw_trend != "up" else 35) * 0.2
        )

        return {
            "foreign": ParticipantView(
                participant="외국인",
                stance="매수 우위" if foreign_bias >= 60 else "중립" if foreign_bias >= 45 else "매도 우위",
                confidence=float(np.clip(foreign_bias, 0, 100)),
                logic=[
                    "수출 사이클과 환율(원화 방향)에 민감",
                    "원화 강세(USDKRW 하락) 구간에서 유입 강도가 높아지는 경향",
                ],
            ),
            "institution": ParticipantView(
                participant="기관",
                stance="매수 우위" if institution_bias >= 60 else "중립" if institution_bias >= 45 else "매도 우위",
                confidence=float(np.clip(institution_bias, 0, 100)),
                logic=[
                    "정책금리 및 밸류에이션 부담에 민감",
                    "금리 하향 안정 시 대형 가치/배당주 선호가 강화되는 경향",
                ],
            ),
            "individual": ParticipantView(
                participant="개인",
                stance="매수 우위" if individual_bias >= 60 else "중립" if individual_bias >= 45 else "매도 우위",
                confidence=float(np.clip(individual_bias, 0, 100)),
                logic=[
                    "위험선호 및 단기 모멘텀 변화에 민감",
                    "테마/성장주 중심의 회전이 빠른 편",
                ],
            ),
        }

    @staticmethod
    def _normalize_market_cap(stocks: List[KoreanStock]) -> Dict[str, float]:
        caps = np.array([max(s.market_cap, 1) for s in stocks], dtype=float)
        min_cap = np.min(caps)
        max_cap = np.max(caps)
        if max_cap == min_cap:
            return {stock.ticker: 50.0 for stock in stocks}
        return {
            stock.ticker: float((cap - min_cap) / (max_cap - min_cap) * 100)
            for stock, cap in zip(stocks, caps)
        }

    @staticmethod
    def recommend_stocks(
        stocks: List[KoreanStock],
        context: MarketContext,
        top_n: int = 5,
    ) -> List[StockRecommendation]:
        if not stocks:
            return []

        participant_views = TopDownParticipantRecommender.analyze_participant_views(context)
        cap_score = TopDownParticipantRecommender._normalize_market_cap(stocks)

        recommendations: List[StockRecommendation] = []
        for stock in stocks:
            flow = InvestorFlowAnalyzer.analyze_investor_flow(stock)
            returns = stock.get_returns()
            momentum = float(np.mean(returns[-20:]) * 10000) if len(returns) >= 20 else 0.0
            momentum = float(np.clip(momentum, -100, 100))
            volatility = float(np.std(returns[-20:]) * 1000) if len(returns) >= 20 else 0.0
            quality = float(np.clip((2.5 - stock.debt_to_equity) * 25 + stock.current_ratio * 10, 0, 100))

            participant_scores = {
                "foreign": float(np.clip(
                    flow["foreign_strength"] * 0.45 + cap_score[stock.ticker] * 0.25 + context.export_cycle_score * 0.3,
                    -100,
                    100,
                )),
                "institution": float(np.clip(
                    flow["institution_strength"] * 0.4 + quality * 0.4 + (100 - volatility) * 0.2,
                    -100,
                    100,
                )),
                "individual": float(np.clip(
                    flow["individual_strength"] * 0.35 + momentum * 0.45 + volatility * 0.2,
                    -100,
                    100,
                )),
            }

            total_score = (
                participant_scores["foreign"] * (participant_views["foreign"].confidence / 100) * 0.35
                + participant_scores["institution"] * (participant_views["institution"].confidence / 100) * 0.35
                + participant_scores["individual"] * (participant_views["individual"].confidence / 100) * 0.30
            )

            reasons = [
                f"외국인 점수 {participant_scores['foreign']:.1f} (수출/시총/수급 반영)",
                f"기관 점수 {participant_scores['institution']:.1f} (퀄리티/변동성/수급 반영)",
                f"개인 점수 {participant_scores['individual']:.1f} (모멘텀/변동성/수급 반영)",
            ]

            recommendations.append(
                StockRecommendation(
                    ticker=stock.ticker,
                    name=stock.name,
                    total_score=float(total_score),
                    participant_scores=participant_scores,
                    reasons=reasons,
                )
            )

        recommendations.sort(key=lambda x: x.total_score, reverse=True)
        return recommendations[:top_n]
