"""
Mock API 클라이언트 (테스트 및 시연용)
실제 API 없이도 시스템 테스트 가능
"""
import random
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from .base_client import BaseAPIClient, MarketData, OrderRequest, OrderResponse


class MockAPIClient(BaseAPIClient):
    """
    Mock API 클라이언트
    실제 거래 없이 시뮬레이션
    """

    def __init__(self, initial_balance: float = 100_000_000):
        super().__init__()
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.holdings = {}  # {ticker: {'quantity': int, 'avg_price': float}}
        self.orders = {}  # {order_id: OrderResponse}

        # 종목별 기준 가격
        self.base_prices = {
            '005930': 70000,   # 삼성전자
            '000660': 130000,  # SK하이닉스
            '035420': 220000,  # NAVER
            '035720': 50000,   # 카카오
            '068270': 170000,  # 셀트리온
        }

    def connect(self) -> bool:
        """API 연결 (Mock)"""
        print("[Mock API] 연결 성공")
        self.is_connected = True
        return True

    def disconnect(self):
        """API 연결 해제 (Mock)"""
        print("[Mock API] 연결 해제")
        self.is_connected = False

    def get_market_data(self, ticker: str) -> Optional[MarketData]:
        """실시간 시세 조회 (Mock)"""
        if ticker not in self.base_prices:
            return None

        base_price = self.base_prices[ticker]

        # 가격 변동 (-2% ~ +2%)
        change_pct = random.uniform(-0.02, 0.02)
        current_price = base_price * (1 + change_pct)

        # OHLC 생성
        high = current_price * random.uniform(1.0, 1.01)
        low = current_price * random.uniform(0.99, 1.0)
        open_price = current_price * random.uniform(0.995, 1.005)

        # 거래량
        volume = random.randint(500000, 2000000)

        # 투자자 수급 (Mock)
        foreign_buy = random.randint(100000, 500000)
        foreign_sell = random.randint(100000, 500000)
        institution_buy = random.randint(80000, 400000)
        institution_sell = random.randint(80000, 400000)
        individual_buy = random.randint(200000, 800000)
        individual_sell = random.randint(200000, 800000)

        program_buy = random.randint(50000, 300000)
        program_sell = random.randint(50000, 300000)

        short_sell_volume = random.randint(10000, 100000)

        return MarketData(
            ticker=ticker,
            timestamp=datetime.now().isoformat(),
            price=current_price,
            open=open_price,
            high=high,
            low=low,
            volume=volume,
            foreign_buy=foreign_buy,
            foreign_sell=foreign_sell,
            institution_buy=institution_buy,
            institution_sell=institution_sell,
            individual_buy=individual_buy,
            individual_sell=individual_sell,
            program_buy=program_buy,
            program_sell=program_sell,
            short_sell_volume=short_sell_volume
        )

    def get_market_data_batch(self, tickers: List[str]) -> Dict[str, MarketData]:
        """여러 종목 시세 일괄 조회 (Mock)"""
        result = {}
        for ticker in tickers:
            data = self.get_market_data(ticker)
            if data:
                result[ticker] = data
        return result

    def get_investor_flow(self, ticker: str) -> Dict:
        """투자자별 수급 정보 조회 (Mock)"""
        data = self.get_market_data(ticker)

        if not data:
            return {}

        return {
            'ticker': ticker,
            'foreign_net': data.foreign_net,
            'institution_net': data.institution_net,
            'foreign_buy': data.foreign_buy,
            'foreign_sell': data.foreign_sell,
            'institution_buy': data.institution_buy,
            'institution_sell': data.institution_sell
        }

    def place_order(self, order: OrderRequest) -> OrderResponse:
        """주문 실행 (Mock)"""
        order_id = str(uuid.uuid4())[:8]

        # 현재 시세 조회
        market_data = self.get_market_data(order.ticker)

        if not market_data:
            return OrderResponse(
                order_id=order_id,
                ticker=order.ticker,
                order_type=order.order_type,
                quantity=order.quantity,
                price=0,
                status="FAILED",
                message="종목 정보를 찾을 수 없습니다"
            )

        # 주문 가격 결정
        if order.order_method == "MARKET" or order.price is None:
            execution_price = market_data.price
        else:
            execution_price = order.price

        # 매수 처리
        if order.order_type == "BUY":
            total_cost = execution_price * order.quantity

            if total_cost > self.balance:
                return OrderResponse(
                    order_id=order_id,
                    ticker=order.ticker,
                    order_type=order.order_type,
                    quantity=order.quantity,
                    price=execution_price,
                    status="FAILED",
                    message="잔고 부족"
                )

            # 잔고 차감
            self.balance -= total_cost

            # 보유 종목에 추가
            if order.ticker in self.holdings:
                old_qty = self.holdings[order.ticker]['quantity']
                old_avg = self.holdings[order.ticker]['avg_price']

                new_qty = old_qty + order.quantity
                new_avg = (old_qty * old_avg + order.quantity * execution_price) / new_qty

                self.holdings[order.ticker]['quantity'] = new_qty
                self.holdings[order.ticker]['avg_price'] = new_avg
            else:
                self.holdings[order.ticker] = {
                    'quantity': order.quantity,
                    'avg_price': execution_price
                }

            message = f"매수 체결: {order.quantity}주 @ {execution_price:,.0f}원"

        # 매도 처리
        elif order.order_type == "SELL":
            if order.ticker not in self.holdings:
                return OrderResponse(
                    order_id=order_id,
                    ticker=order.ticker,
                    order_type=order.order_type,
                    quantity=order.quantity,
                    price=execution_price,
                    status="FAILED",
                    message="보유 종목이 아닙니다"
                )

            if self.holdings[order.ticker]['quantity'] < order.quantity:
                return OrderResponse(
                    order_id=order_id,
                    ticker=order.ticker,
                    order_type=order.order_type,
                    quantity=order.quantity,
                    price=execution_price,
                    status="FAILED",
                    message="보유 수량 부족"
                )

            # 매도 대금 계산 (수수료 및 세금 차감)
            gross_amount = execution_price * order.quantity
            commission = gross_amount * 0.00015  # 0.015%
            tax = gross_amount * 0.0023  # 0.23%
            net_amount = gross_amount - commission - tax

            # 잔고 증가
            self.balance += net_amount

            # 보유 종목에서 차감
            self.holdings[order.ticker]['quantity'] -= order.quantity

            if self.holdings[order.ticker]['quantity'] == 0:
                del self.holdings[order.ticker]

            message = f"매도 체결: {order.quantity}주 @ {execution_price:,.0f}원 (수수료+세금: {commission+tax:,.0f}원)"

        else:
            return OrderResponse(
                order_id=order_id,
                ticker=order.ticker,
                order_type=order.order_type,
                quantity=order.quantity,
                price=execution_price,
                status="FAILED",
                message="잘못된 주문 유형"
            )

        response = OrderResponse(
            order_id=order_id,
            ticker=order.ticker,
            order_type=order.order_type,
            quantity=order.quantity,
            price=execution_price,
            status="SUCCESS",
            message=message
        )

        self.orders[order_id] = response

        return response

    def cancel_order(self, order_id: str) -> bool:
        """주문 취소 (Mock)"""
        if order_id in self.orders:
            print(f"[Mock API] 주문 {order_id} 취소됨")
            return True
        return False

    def get_account_balance(self) -> Dict:
        """계좌 잔고 조회 (Mock)"""
        # 평가 금액 계산
        total_value = self.balance

        for ticker, holding in self.holdings.items():
            market_data = self.get_market_data(ticker)
            if market_data:
                total_value += market_data.price * holding['quantity']

        return {
            'cash_balance': self.balance,
            'stock_value': total_value - self.balance,
            'total_value': total_value,
            'initial_balance': self.initial_balance,
            'profit_loss': total_value - self.initial_balance,
            'profit_loss_pct': ((total_value - self.initial_balance) / self.initial_balance) * 100
        }

    def get_holdings(self) -> Dict[str, Dict]:
        """보유 종목 조회 (Mock)"""
        result = {}

        for ticker, holding in self.holdings.items():
            market_data = self.get_market_data(ticker)

            if market_data:
                current_value = market_data.price * holding['quantity']
                cost = holding['avg_price'] * holding['quantity']
                profit_loss = current_value - cost
                profit_loss_pct = (profit_loss / cost) * 100

                result[ticker] = {
                    'quantity': holding['quantity'],
                    'avg_price': holding['avg_price'],
                    'current_price': market_data.price,
                    'current_value': current_value,
                    'profit_loss': profit_loss,
                    'profit_loss_pct': profit_loss_pct
                }

        return result
