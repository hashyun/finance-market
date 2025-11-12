"""
실시간 데이터 API 클라이언트 베이스 클래스
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MarketData:
    """실시간 시장 데이터"""
    ticker: str
    timestamp: str
    price: float
    open: float
    high: float
    low: float
    volume: int

    # 한국 시장 특화
    foreign_buy: int = 0
    foreign_sell: int = 0
    institution_buy: int = 0
    institution_sell: int = 0
    individual_buy: int = 0
    individual_sell: int = 0

    program_buy: int = 0
    program_sell: int = 0

    short_sell_volume: int = 0

    @property
    def foreign_net(self) -> int:
        return self.foreign_buy - self.foreign_sell

    @property
    def institution_net(self) -> int:
        return self.institution_buy - self.institution_sell


@dataclass
class OrderRequest:
    """주문 요청"""
    ticker: str
    order_type: str  # "BUY" or "SELL"
    quantity: int
    price: Optional[float] = None  # None이면 시장가
    order_method: str = "MARKET"  # "MARKET" or "LIMIT"


@dataclass
class OrderResponse:
    """주문 응답"""
    order_id: str
    ticker: str
    order_type: str
    quantity: int
    price: float
    status: str  # "SUCCESS", "FAILED", "PENDING"
    message: str


class BaseAPIClient(ABC):
    """
    API 클라이언트 추상 베이스 클래스
    실제 증권사 API에 맞게 구현
    """

    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_connected = False

    @abstractmethod
    def connect(self) -> bool:
        """API 연결"""
        pass

    @abstractmethod
    def disconnect(self):
        """API 연결 해제"""
        pass

    @abstractmethod
    def get_market_data(self, ticker: str) -> Optional[MarketData]:
        """실시간 시세 조회"""
        pass

    @abstractmethod
    def get_market_data_batch(self, tickers: List[str]) -> Dict[str, MarketData]:
        """여러 종목 시세 일괄 조회"""
        pass

    @abstractmethod
    def get_investor_flow(self, ticker: str) -> Dict:
        """투자자별 수급 정보 조회"""
        pass

    @abstractmethod
    def place_order(self, order: OrderRequest) -> OrderResponse:
        """주문 실행"""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        pass

    @abstractmethod
    def get_account_balance(self) -> Dict:
        """계좌 잔고 조회"""
        pass

    @abstractmethod
    def get_holdings(self) -> Dict[str, Dict]:
        """보유 종목 조회"""
        pass

    def is_market_open(self) -> bool:
        """장 운영 시간 확인"""
        now = datetime.now()

        # 주말 제외
        if now.weekday() >= 5:
            return False

        # 9:00 ~ 15:30 (한국 시장)
        market_open = now.replace(hour=9, minute=0, second=0)
        market_close = now.replace(hour=15, minute=30, second=0)

        return market_open <= now <= market_close
