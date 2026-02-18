import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.analysis.top_down_recommender import MarketContext, TopDownParticipantRecommender
from src.models.korean_stock import KoreanStock, TradingData


def _make_stock(ticker: str, name: str, market_cap: float, foreign_bias: int, inst_bias: int, ind_bias: int) -> KoreanStock:
    trading_data = []
    base_price = 10000
    for i in range(30):
        price = base_price + i * 20
        volume = 1_000_000 + i * 5000
        trading_data.append(
            TradingData(
                date=f"2025-01-{i+1:02d}",
                open=price,
                high=price * 1.01,
                low=price * 0.99,
                close=price,
                volume=volume,
                foreign_buy=50000 + foreign_bias,
                foreign_sell=40000,
                institution_buy=45000 + inst_bias,
                institution_sell=40000,
                individual_buy=60000 + ind_bias,
                individual_sell=55000,
            )
        )

    return KoreanStock(
        ticker=ticker,
        name=name,
        sector="IT",
        market="KOSPI",
        trading_data=trading_data,
        market_cap=market_cap,
        debt_to_equity=0.5,
        current_ratio=2.0,
    )


def test_participant_view_and_recommendation_order():
    context = MarketContext(
        risk_on_score=70,
        usdkrw_trend="down",
        policy_rate_direction="down",
        export_cycle_score=75,
    )

    stocks = [
        _make_stock("005930", "삼성전자", 500_000_000_000_000, 20000, 12000, 7000),
        _make_stock("000660", "SK하이닉스", 120_000_000_000_000, 8000, 6000, 5000),
        _make_stock("035420", "NAVER", 35_000_000_000_000, 3000, 2000, 1000),
    ]

    views = TopDownParticipantRecommender.analyze_participant_views(context)
    assert views["foreign"].stance in {"매수 우위", "중립", "매도 우위"}
    assert views["foreign"].confidence > 0

    recs = TopDownParticipantRecommender.recommend_stocks(stocks, context, top_n=3)
    assert len(recs) == 3
    assert recs[0].total_score >= recs[1].total_score >= recs[2].total_score
    assert all("foreign" in rec.participant_scores for rec in recs)
