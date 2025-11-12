"""
KRX (한국거래소) API 클라이언트
실제 시장 데이터를 가져오는 클라이언트
"""
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .base_client import BaseAPIClient, MarketData, OrderRequest, OrderResponse


class KRXAPIClient(BaseAPIClient):
    """
    KRX API 클라이언트
    - KRX에서 시장 데이터 가져오기
    - 네이버/다음 금융 API 활용 (보조)
    - 포지션은 파일로 관리 (수동 매매)
    """

    def __init__(self, position_file: str = "data/my_positions.json"):
        """
        Args:
            position_file: 포지션 정보 파일 경로
        """
        self.position_file = position_file
        self.positions = {}
        self.is_connected = False

        # KRX API 엔드포인트
        self.krx_base_url = "http://data.krx.co.kr"

        # 네이버 금융 API (시세 조회용)
        self.naver_finance_url = "https://m.stock.naver.com/api"

    def connect(self):
        """API 연결 및 포지션 파일 로드"""
        print("KRX API 연결 중...")

        # 포지션 파일 로드
        try:
            with open(self.position_file, 'r', encoding='utf-8') as f:
                self.positions = json.load(f)
            print(f"포지션 파일 로드 완료: {len(self.positions)}개 종목")
        except FileNotFoundError:
            print(f"포지션 파일이 없습니다: {self.position_file}")
            print("빈 포지션으로 시작합니다.")
            self.positions = {}
        except json.JSONDecodeError:
            print(f"포지션 파일 형식 오류: {self.position_file}")
            self.positions = {}

        self.is_connected = True
        print("연결 완료")

    def disconnect(self):
        """연결 해제"""
        self.is_connected = False
        print("연결 해제")

    def is_market_open(self) -> bool:
        """장 운영 시간 확인"""
        now = datetime.now()

        # 주말 제외
        if now.weekday() >= 5:
            return False

        # 평일 9:00 ~ 15:30
        market_open = now.replace(hour=9, minute=0, second=0)
        market_close = now.replace(hour=15, minute=30, second=0)

        return market_open <= now <= market_close

    def get_market_data(self, ticker: str) -> Optional[MarketData]:
        """
        실시간 시세 조회 (네이버 금융 API 활용)

        Args:
            ticker: 종목코드

        Returns:
            시장 데이터
        """
        try:
            # 네이버 금융 API로 현재가 조회
            url = f"{self.naver_finance_url}/stock/{ticker}/basic"
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                print(f"시세 조회 실패: {ticker}")
                return None

            data = response.json()

            # 투자자별 매매동향 조회 (별도 API)
            investor_data = self._get_investor_trading(ticker)

            return MarketData(
                ticker=ticker,
                timestamp=datetime.now().isoformat(),
                price=float(data.get('closePrice', 0)),
                volume=int(data.get('accumulatedTradingVolume', 0)),
                foreign_buy=investor_data.get('foreign_buy', 0),
                foreign_sell=investor_data.get('foreign_sell', 0),
                foreign_net=investor_data.get('foreign_net', 0),
                institution_buy=investor_data.get('institution_buy', 0),
                institution_sell=investor_data.get('institution_sell', 0),
                institution_net=investor_data.get('institution_net', 0),
                individual_buy=investor_data.get('individual_buy', 0),
                individual_sell=investor_data.get('individual_sell', 0),
                individual_net=investor_data.get('individual_net', 0),
                program_buy=0,  # 프로그램 매매는 KRX에서 별도 조회 필요
                program_sell=0,
                program_net=0
            )

        except Exception as e:
            print(f"시세 조회 오류 ({ticker}): {e}")
            return None

    def _get_investor_trading(self, ticker: str) -> Dict:
        """
        투자자별 매매동향 조회

        Args:
            ticker: 종목코드

        Returns:
            투자자별 매매 데이터
        """
        try:
            # 네이버 금융에서 투자자별 매매 데이터 조회
            url = f"{self.naver_finance_url}/stock/{ticker}/investor"
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                return {}

            data = response.json()

            # 최근 데이터 파싱
            if not data or 'investorTrendList' not in data:
                return {}

            recent = data['investorTrendList'][0] if data['investorTrendList'] else {}

            return {
                'foreign_buy': int(recent.get('foreignBuyVolume', 0)),
                'foreign_sell': int(recent.get('foreignSellVolume', 0)),
                'foreign_net': int(recent.get('foreignNetVolume', 0)),
                'institution_buy': int(recent.get('institutionBuyVolume', 0)),
                'institution_sell': int(recent.get('institutionSellVolume', 0)),
                'institution_net': int(recent.get('institutionNetVolume', 0)),
                'individual_buy': int(recent.get('individualBuyVolume', 0)),
                'individual_sell': int(recent.get('individualSellVolume', 0)),
                'individual_net': int(recent.get('individualNetVolume', 0))
            }

        except Exception as e:
            print(f"투자자 매매동향 조회 오류: {e}")
            return {}

    def get_market_data_batch(self, tickers: List[str]) -> Dict[str, MarketData]:
        """
        여러 종목 시세 일괄 조회

        Args:
            tickers: 종목코드 리스트

        Returns:
            {ticker: MarketData} 딕셔너리
        """
        result = {}

        for ticker in tickers:
            market_data = self.get_market_data(ticker)
            if market_data:
                result[ticker] = market_data

        return result

    def get_account_balance(self) -> Dict:
        """
        계좌 잔고 조회 (포지션 파일 기반)

        Returns:
            계좌 정보
        """
        if not self.positions:
            return {
                'cash_balance': 0,
                'stock_value': 0,
                'total_value': 0,
                'profit_loss': 0,
                'profit_loss_pct': 0
            }

        # 현금 잔고
        cash_balance = self.positions.get('cash', 0)

        # 주식 평가액 계산
        stock_value = 0
        total_cost = 0

        holdings = self.positions.get('holdings', {})

        for ticker, position in holdings.items():
            # 실시간 시세 조회
            market_data = self.get_market_data(ticker)

            if market_data:
                current_price = market_data.price
            else:
                # 시세 조회 실패 시 평균단가 사용
                current_price = position['avg_price']

            quantity = position['quantity']
            avg_price = position['avg_price']

            stock_value += current_price * quantity
            total_cost += avg_price * quantity

        # 총 자산
        total_value = cash_balance + stock_value

        # 손익
        profit_loss = stock_value - total_cost
        profit_loss_pct = (profit_loss / total_cost * 100) if total_cost > 0 else 0

        return {
            'cash_balance': cash_balance,
            'stock_value': stock_value,
            'total_value': total_value,
            'profit_loss': profit_loss,
            'profit_loss_pct': profit_loss_pct
        }

    def get_holdings(self) -> Dict:
        """
        보유 종목 조회 (포지션 파일 기반)

        Returns:
            보유 종목 정보
        """
        holdings = {}

        position_holdings = self.positions.get('holdings', {})

        for ticker, position in position_holdings.items():
            # 실시간 시세 조회
            market_data = self.get_market_data(ticker)

            if market_data:
                current_price = market_data.price
            else:
                current_price = position['avg_price']

            quantity = position['quantity']
            avg_price = position['avg_price']

            current_value = current_price * quantity
            cost = avg_price * quantity
            profit_loss = current_value - cost
            profit_loss_pct = (profit_loss / cost * 100) if cost > 0 else 0

            holdings[ticker] = {
                'quantity': quantity,
                'avg_price': avg_price,
                'current_price': current_price,
                'current_value': current_value,
                'cost': cost,
                'profit_loss': profit_loss,
                'profit_loss_pct': profit_loss_pct
            }

        return holdings

    def place_order(self, order: OrderRequest) -> OrderResponse:
        """
        주문 실행 (수동 매매이므로 추천만 출력)

        Args:
            order: 주문 정보

        Returns:
            주문 응답 (실제 주문 안됨)
        """
        # 실제 주문은 하지 않고 추천만 출력
        market_data = self.get_market_data(order.ticker)

        if not market_data:
            return OrderResponse(
                order_id="MANUAL",
                status="FAILED",
                message="시세 조회 실패",
                ticker=order.ticker,
                order_type=order.order_type,
                quantity=0,
                price=0,
                timestamp=datetime.now().isoformat()
            )

        price = market_data.price

        return OrderResponse(
            order_id="MANUAL",
            status="RECOMMENDATION",
            message=f"[수동 매매 추천] {order.order_type} {order.ticker} {order.quantity}주 @ {price:,.0f}원",
            ticker=order.ticker,
            order_type=order.order_type,
            quantity=order.quantity,
            price=price,
            timestamp=datetime.now().isoformat()
        )

    def update_position_file(self, positions: Dict):
        """
        포지션 파일 업데이트

        Args:
            positions: 업데이트할 포지션 데이터
        """
        self.positions = positions

        try:
            with open(self.position_file, 'w', encoding='utf-8') as f:
                json.dump(positions, f, ensure_ascii=False, indent=2)
            print(f"포지션 파일 업데이트 완료: {self.position_file}")
        except Exception as e:
            print(f"포지션 파일 업데이트 실패: {e}")

    def save_positions(self):
        """현재 포지션을 파일에 저장"""
        self.update_position_file(self.positions)
