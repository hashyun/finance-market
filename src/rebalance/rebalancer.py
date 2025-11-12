"""
포트폴리오 자동 리밸런싱 엔진
"""
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from ..api.base_client import BaseAPIClient, OrderRequest
from ..strategies.base_strategy import BaseStrategy


@dataclass
class RebalanceResult:
    """리밸런싱 결과"""
    timestamp: str
    trigger_reason: str
    orders_executed: List[Dict]
    success: bool
    message: str


class PortfolioRebalancer:
    """
    자동 리밸런싱 엔진
    """

    def __init__(
        self,
        api_client: BaseAPIClient,
        strategy: BaseStrategy,
        target_tickers: List[str],
        rebalance_threshold: float = 0.05,  # 5% 이상 벗어나면 리밸런싱
        min_trade_amount: float = 100_000,  # 최소 거래 금액 (10만원)
        max_position_size: float = 0.4  # 최대 포지션 크기 (40%)
    ):
        """
        Args:
            api_client: API 클라이언트
            strategy: 트레이딩 전략
            target_tickers: 대상 종목 리스트
            rebalance_threshold: 리밸런싱 임계값
            min_trade_amount: 최소 거래 금액
            max_position_size: 최대 포지션 크기
        """
        self.api_client = api_client
        self.strategy = strategy
        self.target_tickers = target_tickers
        self.rebalance_threshold = rebalance_threshold
        self.min_trade_amount = min_trade_amount
        self.max_position_size = max_position_size

    def calculate_target_weights(self) -> Dict[str, float]:
        """
        전략을 기반으로 목표 비중 계산

        Returns:
            {ticker: target_weight} 딕셔너리
        """
        # 모든 종목 점수 계산
        scores = {}

        for ticker in self.target_tickers:
            try:
                # 실시간 데이터로 임시 주식 객체 생성 필요
                # 여기서는 간단히 전략 점수만 사용
                # 실제로는 KoreanStock 객체를 생성해야 함
                score = 50.0  # 기본값
                scores[ticker] = max(score, 0)  # 음수 점수는 0으로
            except Exception as e:
                scores[ticker] = 0

        # 점수 합계
        total_score = sum(scores.values())

        if total_score == 0:
            # 모든 점수가 0이면 동일 비중
            n = len(self.target_tickers)
            return {ticker: 1.0 / n for ticker in self.target_tickers}

        # 점수 비율로 비중 계산
        weights = {}
        for ticker, score in scores.items():
            weight = score / total_score

            # 최대 포지션 크기 제한
            weight = min(weight, self.max_position_size)

            weights[ticker] = weight

        # 비중 재정규화
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        return weights

    def get_current_weights(self) -> Dict[str, float]:
        """
        현재 포트폴리오 비중 계산

        Returns:
            {ticker: current_weight} 딕셔너리
        """
        holdings = self.api_client.get_holdings()
        account = self.api_client.get_account_balance()

        total_value = account['total_value']

        if total_value == 0:
            return {}

        current_weights = {}

        for ticker in self.target_tickers:
            if ticker in holdings:
                position_value = holdings[ticker]['current_value']
                current_weights[ticker] = position_value / total_value
            else:
                current_weights[ticker] = 0.0

        return current_weights

    def needs_rebalancing(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float]
    ) -> bool:
        """
        리밸런싱 필요 여부 판단

        Args:
            current_weights: 현재 비중
            target_weights: 목표 비중

        Returns:
            리밸런싱 필요 여부
        """
        for ticker in self.target_tickers:
            current = current_weights.get(ticker, 0)
            target = target_weights.get(ticker, 0)

            deviation = abs(current - target)

            # 임계값 초과 시 리밸런싱 필요
            if deviation > self.rebalance_threshold:
                return True

        return False

    def execute_rebalancing(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float]
    ) -> RebalanceResult:
        """
        리밸런싱 실행

        Args:
            current_weights: 현재 비중
            target_weights: 목표 비중

        Returns:
            리밸런싱 결과
        """
        orders_executed = []

        try:
            account = self.api_client.get_account_balance()
            total_value = account['total_value']
            holdings = self.api_client.get_holdings()

            # 현재 시세 조회
            market_data_batch = self.api_client.get_market_data_batch(self.target_tickers)

            # 1단계: 비중 줄일 종목 먼저 매도
            for ticker in self.target_tickers:
                current = current_weights.get(ticker, 0)
                target = target_weights.get(ticker, 0)

                if current > target:
                    # 매도 필요
                    if ticker not in holdings:
                        continue

                    if ticker not in market_data_batch:
                        continue

                    current_price = market_data_batch[ticker].price
                    current_quantity = holdings[ticker]['quantity']

                    # 목표 비중에 맞는 수량 계산
                    target_value = total_value * target
                    target_quantity = int(target_value / current_price)

                    sell_quantity = current_quantity - target_quantity

                    # 최소 거래 금액 확인
                    if sell_quantity * current_price < self.min_trade_amount:
                        continue

                    # 매도 주문
                    order = OrderRequest(
                        ticker=ticker,
                        order_type="SELL",
                        quantity=sell_quantity,
                        order_method="MARKET"
                    )

                    response = self.api_client.place_order(order)

                    orders_executed.append({
                        'ticker': ticker,
                        'order_type': 'SELL',
                        'quantity': sell_quantity,
                        'price': response.price,
                        'status': response.status,
                        'message': response.message
                    })

                    # 약간의 지연 (실제 API에서는 필요할 수 있음)
                    time.sleep(0.1)

            # 잔고 업데이트
            account = self.api_client.get_account_balance()
            available_cash = account['cash_balance']

            # 2단계: 비중 늘릴 종목 매수
            for ticker in self.target_tickers:
                current = current_weights.get(ticker, 0)
                target = target_weights.get(ticker, 0)

                if current < target:
                    # 매수 필요
                    if ticker not in market_data_batch:
                        continue

                    current_price = market_data_batch[ticker].price

                    # 목표 비중에 맞는 수량 계산
                    target_value = total_value * target
                    current_value = holdings.get(ticker, {}).get('current_value', 0)

                    buy_value = target_value - current_value

                    # 최소 거래 금액 확인
                    if buy_value < self.min_trade_amount:
                        continue

                    # 사용 가능한 금액 확인
                    buy_value = min(buy_value, available_cash)

                    if buy_value < self.min_trade_amount:
                        continue

                    buy_quantity = int(buy_value / current_price)

                    if buy_quantity == 0:
                        continue

                    # 매수 주문
                    order = OrderRequest(
                        ticker=ticker,
                        order_type="BUY",
                        quantity=buy_quantity,
                        order_method="MARKET"
                    )

                    response = self.api_client.place_order(order)

                    orders_executed.append({
                        'ticker': ticker,
                        'order_type': 'BUY',
                        'quantity': buy_quantity,
                        'price': response.price,
                        'status': response.status,
                        'message': response.message
                    })

                    # 잔고 차감
                    if response.status == "SUCCESS":
                        available_cash -= buy_quantity * response.price

                    time.sleep(0.1)

            return RebalanceResult(
                timestamp=datetime.now().isoformat(),
                trigger_reason="임계값 초과",
                orders_executed=orders_executed,
                success=True,
                message=f"리밸런싱 완료: {len(orders_executed)}개 주문 실행"
            )

        except Exception as e:
            return RebalanceResult(
                timestamp=datetime.now().isoformat(),
                trigger_reason="임계값 초과",
                orders_executed=orders_executed,
                success=False,
                message=f"리밸런싱 실패: {str(e)}"
            )

    def run_rebalancing_check(self) -> Optional[RebalanceResult]:
        """
        리밸런싱 필요 여부 확인 및 실행

        Returns:
            리밸런싱 결과 (실행되지 않으면 None)
        """
        # 장 운영 시간 확인
        if not self.api_client.is_market_open():
            return None

        # 현재 비중 계산
        current_weights = self.get_current_weights()

        # 목표 비중 계산
        target_weights = self.calculate_target_weights()

        # 리밸런싱 필요 여부 확인
        if not self.needs_rebalancing(current_weights, target_weights):
            return None

        # 리밸런싱 실행
        result = self.execute_rebalancing(current_weights, target_weights)

        return result

    def get_rebalancing_preview(self) -> Dict:
        """
        리밸런싱 미리보기 (실제 주문 없이)

        Returns:
            리밸런싱 계획
        """
        current_weights = self.get_current_weights()
        target_weights = self.calculate_target_weights()

        preview = {
            'current_weights': current_weights,
            'target_weights': target_weights,
            'needs_rebalancing': self.needs_rebalancing(current_weights, target_weights),
            'deviations': {}
        }

        for ticker in self.target_tickers:
            current = current_weights.get(ticker, 0)
            target = target_weights.get(ticker, 0)
            deviation = target - current

            preview['deviations'][ticker] = {
                'current': current,
                'target': target,
                'deviation': deviation,
                'action': 'BUY' if deviation > 0 else 'SELL' if deviation < 0 else 'HOLD'
            }

        return preview
