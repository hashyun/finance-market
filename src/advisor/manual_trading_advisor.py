"""
수동 매매를 위한 트레이딩 어드바이저
리밸런싱 추천 및 매매 가이드 제공
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from ..api.base_client import BaseAPIClient
from ..strategies.base_strategy import BaseStrategy


@dataclass
class TradingRecommendation:
    """매매 추천"""
    ticker: str
    action: str  # BUY, SELL, HOLD
    current_weight: float
    target_weight: float
    deviation: float
    current_quantity: int
    recommended_quantity: int  # 매수/매도할 수량
    estimated_price: float
    estimated_amount: float
    reason: str
    priority: int  # 1(높음) ~ 3(낮음)


class ManualTradingAdvisor:
    """
    수동 매매 어드바이저
    - 포트폴리오 분석
    - 리밸런싱 추천
    - 매매 가이드 제공
    """

    def __init__(
        self,
        api_client: BaseAPIClient,
        strategy: BaseStrategy,
        target_tickers: List[str],
        rebalance_threshold: float = 0.05,
        min_trade_amount: float = 100_000,
        max_position_size: float = 0.3
    ):
        """
        Args:
            api_client: API 클라이언트
            strategy: 트레이딩 전략
            target_tickers: 대상 종목
            rebalance_threshold: 리밸런싱 임계값 (5%)
            min_trade_amount: 최소 거래 금액
            max_position_size: 최대 포지션 크기
        """
        self.api_client = api_client
        self.strategy = strategy
        self.target_tickers = target_tickers
        self.rebalance_threshold = rebalance_threshold
        self.min_trade_amount = min_trade_amount
        self.max_position_size = max_position_size

    def get_portfolio_analysis(self) -> Dict:
        """
        포트폴리오 분석

        Returns:
            분석 결과
        """
        account = self.api_client.get_account_balance()
        holdings = self.api_client.get_holdings()

        total_value = account['total_value']
        cash_balance = account['cash_balance']

        # 현재 비중
        current_weights = {}
        for ticker in self.target_tickers:
            if ticker in holdings:
                position_value = holdings[ticker]['current_value']
                current_weights[ticker] = position_value / total_value if total_value > 0 else 0
            else:
                current_weights[ticker] = 0.0

        # 목표 비중 (전략 기반)
        target_weights = self._calculate_target_weights()

        # 비중 차이
        deviations = {}
        for ticker in self.target_tickers:
            current = current_weights.get(ticker, 0)
            target = target_weights.get(ticker, 0)
            deviations[ticker] = target - current

        # 리밸런싱 필요 여부
        needs_rebalancing = any(abs(dev) > self.rebalance_threshold for dev in deviations.values())

        return {
            'timestamp': datetime.now().isoformat(),
            'total_value': total_value,
            'cash_balance': cash_balance,
            'stock_value': account['stock_value'],
            'profit_loss': account['profit_loss'],
            'profit_loss_pct': account['profit_loss_pct'],
            'current_weights': current_weights,
            'target_weights': target_weights,
            'deviations': deviations,
            'needs_rebalancing': needs_rebalancing,
            'rebalance_threshold': self.rebalance_threshold
        }

    def get_trading_recommendations(self) -> List[TradingRecommendation]:
        """
        매매 추천 생성

        Returns:
            매매 추천 리스트
        """
        recommendations = []

        account = self.api_client.get_account_balance()
        holdings = self.api_client.get_holdings()
        total_value = account['total_value']

        # 현재 비중
        current_weights = {}
        for ticker in self.target_tickers:
            if ticker in holdings:
                current_weights[ticker] = holdings[ticker]['current_value'] / total_value if total_value > 0 else 0
            else:
                current_weights[ticker] = 0.0

        # 목표 비중
        target_weights = self._calculate_target_weights()

        # 시세 조회
        market_data_batch = self.api_client.get_market_data_batch(self.target_tickers)

        for ticker in self.target_tickers:
            current = current_weights.get(ticker, 0)
            target = target_weights.get(ticker, 0)
            deviation = target - current

            # 시세 확인
            if ticker not in market_data_batch:
                continue

            current_price = market_data_batch[ticker].price

            # 현재 보유 수량
            current_quantity = holdings.get(ticker, {}).get('quantity', 0)

            # 목표 수량
            target_value = total_value * target
            target_quantity = int(target_value / current_price)

            # 매수/매도 수량
            recommended_quantity = target_quantity - current_quantity

            # 최소 거래 금액 미만이면 스킵
            estimated_amount = abs(recommended_quantity * current_price)
            if estimated_amount < self.min_trade_amount:
                continue

            # 액션 결정
            if deviation > self.rebalance_threshold:
                action = "BUY"
                reason = f"목표 비중({target:.1%})보다 {abs(deviation):.1%}p 낮음"
                priority = 1 if abs(deviation) > 0.1 else 2
            elif deviation < -self.rebalance_threshold:
                action = "SELL"
                reason = f"목표 비중({target:.1%})보다 {abs(deviation):.1%}p 높음"
                priority = 1 if abs(deviation) > 0.1 else 2
            else:
                action = "HOLD"
                reason = f"목표 비중({target:.1%})과 유사"
                priority = 3

            recommendations.append(TradingRecommendation(
                ticker=ticker,
                action=action,
                current_weight=current,
                target_weight=target,
                deviation=deviation,
                current_quantity=current_quantity,
                recommended_quantity=abs(recommended_quantity),
                estimated_price=current_price,
                estimated_amount=estimated_amount,
                reason=reason,
                priority=priority
            ))

        # 우선순위로 정렬
        recommendations.sort(key=lambda x: (x.priority, -abs(x.deviation)))

        return recommendations

    def print_trading_guide(self):
        """매매 가이드 출력"""
        print("\n" + "="*90)
        print("  포트폴리오 분석 및 매매 가이드")
        print("="*90)

        # 포트폴리오 분석
        analysis = self.get_portfolio_analysis()

        print("\n[계좌 현황]")
        print(f"  총 자산:          {analysis['total_value']:>15,.0f}원")
        print(f"  현금 잔고:        {analysis['cash_balance']:>15,.0f}원 ({analysis['cash_balance']/analysis['total_value']*100:.1f}%)")
        print(f"  주식 평가액:      {analysis['stock_value']:>15,.0f}원 ({analysis['stock_value']/analysis['total_value']*100:.1f}%)")
        print(f"  손익:             {analysis['profit_loss']:>15,.0f}원 ({analysis['profit_loss_pct']:+.2f}%)")

        print("\n[포트폴리오 비중]")
        print(f"  {'종목':10} {'현재비중':>12} {'목표비중':>12} {'차이':>12} {'상태':>12}")
        print("  " + "-"*65)

        for ticker in self.target_tickers:
            current = analysis['current_weights'].get(ticker, 0)
            target = analysis['target_weights'].get(ticker, 0)
            deviation = analysis['deviations'].get(ticker, 0)

            status = "🔴 매수필요" if deviation > self.rebalance_threshold else \
                     "🔵 매도필요" if deviation < -self.rebalance_threshold else \
                     "✅ 적정"

            print(f"  {ticker:10} "
                  f"{current:>11.1%} "
                  f"{target:>11.1%} "
                  f"{deviation:>+11.1%} "
                  f"{status:>12}")

        # 매매 추천
        recommendations = self.get_trading_recommendations()

        if not recommendations:
            print("\n[매매 추천]")
            print("  ✅ 리밸런싱이 필요하지 않습니다.")
            print("\n" + "="*90)
            return

        print(f"\n[리밸런싱 필요 여부]")
        print(f"  임계값: {self.rebalance_threshold:.1%} | 상태: ⚠️ 리밸런싱 필요")

        # 매도 추천
        sell_recs = [r for r in recommendations if r.action == "SELL"]
        if sell_recs:
            print("\n" + "="*90)
            print("  📉 매도 추천")
            print("="*90)
            print(f"  {'종목코드':10} {'종목명':10} {'수량':>10} {'가격':>12} {'예상금액':>15} {'우선순위':>8}")
            print("  " + "-"*86)

            for rec in sell_recs:
                holdings = self.api_client.get_holdings()
                ticker_info = self.api_client.positions['holdings'].get(rec.ticker, {})
                name = ticker_info.get('name', rec.ticker)
                priority_text = "높음" if rec.priority == 1 else "중간" if rec.priority == 2 else "낮음"

                print(f"  {rec.ticker:10} "
                      f"{name:10} "
                      f"{rec.recommended_quantity:>10,}주 "
                      f"{rec.estimated_price:>12,.0f}원 "
                      f"{rec.estimated_amount:>15,.0f}원 "
                      f"{priority_text:>8}")

        # 매수 추천
        buy_recs = [r for r in recommendations if r.action == "BUY"]
        if buy_recs:
            print("\n" + "="*90)
            print("  📈 매수 추천")
            print("="*90)
            print(f"  {'종목코드':10} {'종목명':10} {'수량':>10} {'가격':>12} {'예상금액':>15} {'우선순위':>8}")
            print("  " + "-"*86)

            for rec in buy_recs:
                ticker_info = self.api_client.positions['holdings'].get(rec.ticker, {})
                name = ticker_info.get('name', rec.ticker)
                priority_text = "높음" if rec.priority == 1 else "중간" if rec.priority == 2 else "낮음"

                print(f"  {rec.ticker:10} "
                      f"{name:10} "
                      f"{rec.recommended_quantity:>10,}주 "
                      f"{rec.estimated_price:>12,.0f}원 "
                      f"{rec.estimated_amount:>15,.0f}원 "
                      f"{priority_text:>8}")

        # 요약
        total_sell = sum(r.estimated_amount for r in sell_recs)
        total_buy = sum(r.estimated_amount for r in buy_recs)

        print("\n" + "="*90)
        print("  💰 거래 요약")
        print("="*90)
        print(f"  총 매도 예상액:   {total_sell:>15,.0f}원")
        print(f"  총 매수 예상액:   {total_buy:>15,.0f}원")
        print(f"  순 현금 변동:     {total_sell - total_buy:>+15,.0f}원")

        # 실행 안내
        print("\n  💡 실행 순서:")
        print("     1️⃣  매도 주문 먼저 실행 → 현금 확보")
        print("     2️⃣  매도 체결 확인")
        print("     3️⃣  매수 주문 실행")
        print("     4️⃣  포지션 파일(data/my_positions.json) 업데이트")

        print("\n" + "="*90)

    def _calculate_target_weights(self) -> Dict[str, float]:
        """
        목표 비중 계산 (점수 기반 차등 배분)

        Returns:
            {ticker: weight}
        """
        n = len(self.target_tickers)
        if n == 0:
            return {}

        # 5개 종목만 선택 (이미 선택되었다고 가정하지만, 혹시 모르니 제한)
        tickers = self.target_tickers[:5]

        # 점수 기반 비중 계산을 위해 전략 사용
        # 실제 구현에서는 strategy.calculate_score를 사용해야 하지만
        # 여기서는 간단히 랭킹 기반 차등 배분 사용

        # 5개 종목일 경우: 30%, 25%, 20%, 15%, 10%
        # 더 적은 경우에도 대응
        if len(tickers) == 5:
            base_weights = [0.30, 0.25, 0.20, 0.15, 0.10]
        elif len(tickers) == 4:
            base_weights = [0.30, 0.25, 0.25, 0.20]
        elif len(tickers) == 3:
            base_weights = [0.40, 0.35, 0.25]
        elif len(tickers) == 2:
            base_weights = [0.55, 0.45]
        else:
            base_weights = [1.0]

        weights = {}
        for i, ticker in enumerate(tickers):
            if i < len(base_weights):
                weights[ticker] = base_weights[i]
            else:
                weights[ticker] = 0.10  # 기본값

        # 최대 포지션 크기 제한 적용
        for ticker in weights:
            weights[ticker] = min(weights[ticker], self.max_position_size)

        # 재정규화 (비중 합이 1이 되도록)
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return weights

    def export_recommendations_to_file(self, filename: str = "data/trading_recommendations.json"):
        """
        매매 추천을 파일로 저장

        Args:
            filename: 저장할 파일 경로
        """
        import json

        analysis = self.get_portfolio_analysis()
        recommendations = self.get_trading_recommendations()

        data = {
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis,
            'recommendations': [
                {
                    'ticker': r.ticker,
                    'action': r.action,
                    'current_weight': r.current_weight,
                    'target_weight': r.target_weight,
                    'deviation': r.deviation,
                    'current_quantity': r.current_quantity,
                    'recommended_quantity': r.recommended_quantity,
                    'estimated_price': r.estimated_price,
                    'estimated_amount': r.estimated_amount,
                    'reason': r.reason,
                    'priority': r.priority
                }
                for r in recommendations
            ]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n매매 추천이 파일로 저장되었습니다: {filename}")
