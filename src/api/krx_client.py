"""
KRX (한국거래소) API 클라이언트
pykrx 라이브러리를 사용하여 실제 KRX 데이터를 가져옵니다
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .base_client import BaseAPIClient, MarketData, OrderRequest, OrderResponse


class KRXAPIClient(BaseAPIClient):
    """
    KRX API 클라이언트 (pykrx 기반)
    - pykrx로 실제 KRX 데이터 조회
    - 포지션은 파일로 관리 (수동 매매)
    """

    def __init__(
        self,
        position_file: str = "data/my_positions.json",
        dart_api_key: Optional[str] = None
    ):
        """
        Args:
            position_file: 포지션 정보 파일 경로
            dart_api_key: DART API 키 (선택사항)
        """
        self.position_file = position_file
        self.dart_api_key = dart_api_key or self._load_env_variable('DART_API_KEY')
        self.positions = {}
        self.is_connected = False

        # pykrx import
        try:
            from pykrx import stock
            self.stock = stock
            self.pykrx_available = True
        except ImportError:
            print("❌ pykrx가 설치되어 있지 않습니다.")
            print("   설치: pip install pykrx")
            self.stock = None
            self.pykrx_available = False

        # 가격 캐시
        self.price_cache = {}

    def _load_env_variable(self, key: str) -> Optional[str]:
        """환경변수 또는 .env 파일에서 값 읽기"""
        value = os.environ.get(key)
        if value:
            return value

        env_file = '.env'
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            env_key, env_value = line.split('=', 1)
                            if env_key.strip() == key:
                                return env_value.strip()
            except Exception:
                pass

        return None

    def connect(self):
        """API 연결 및 포지션 파일 로드"""
        print("KRX API 연결 중...")

        if not self.pykrx_available:
            print("❌ pykrx를 설치해주세요: pip install pykrx")
            return

        # 포지션 파일 로드
        try:
            with open(self.position_file, 'r', encoding='utf-8') as f:
                self.positions = json.load(f)
            print(f"✅ 포지션 파일 로드 완료: {len(self.positions.get('holdings', {}))}개 종목")
        except FileNotFoundError:
            print(f"⚠️  포지션 파일이 없습니다: {self.position_file}")
            print("   빈 포지션으로 시작합니다.")
            self.positions = {"cash": 0, "holdings": {}}
        except json.JSONDecodeError:
            print(f"❌ 포지션 파일 형식 오류: {self.position_file}")
            self.positions = {"cash": 0, "holdings": {}}

        self.is_connected = True
        print("✅ 연결 완료 (pykrx를 통해 KRX 데이터 조회)")

    def disconnect(self):
        """연결 해제"""
        self.is_connected = False
        print("연결 해제")

    def is_market_open(self) -> bool:
        """장 운영 시간 확인"""
        now = datetime.now()
        if now.weekday() >= 5:  # 주말
            return False
        market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        return market_open <= now <= market_close

    def get_market_data(self, ticker: str) -> Optional[MarketData]:
        """
        KRX에서 시세 조회 (pykrx 사용)

        Args:
            ticker: 종목코드

        Returns:
            시장 데이터
        """
        if not self.pykrx_available:
            print(f"❌ pykrx가 설치되지 않아 시세를 조회할 수 없습니다.")
            return None

        # 캐시 확인 (5분)
        if ticker in self.price_cache:
            cache_time, data = self.price_cache[ticker]
            if (datetime.now() - cache_time).seconds < 300:
                return data

        try:
            # 최근 30거래일 데이터 조회
            end_date = datetime.now()
            start_date = end_date - timedelta(days=40)

            end_str = end_date.strftime("%Y%m%d")
            start_str = start_date.strftime("%Y%m%d")

            # OHLCV 데이터 조회
            df = self.stock.get_market_ohlcv_by_date(start_str, end_str, ticker)

            if df.empty:
                print(f"⚠️  {ticker}: pykrx 데이터 없음, CSV 파일 확인 중...")
                return self._load_from_csv(ticker)

            # 최신 데이터
            latest = df.iloc[-1]

            # 투자자별 매매 동향 조회
            try:
                investor_df = self.stock.get_market_trading_value_by_date(
                    start_str, end_str, ticker
                )

                if not investor_df.empty:
                    investor_latest = investor_df.iloc[-1]

                    # 거래대금을 수량으로 환산 (대략적)
                    price = latest['종가']
                    foreign_net = int(investor_latest.get('외국인합계', 0) / price) if price > 0 else 0
                    institution_net = int(investor_latest.get('기관합계', 0) / price) if price > 0 else 0
                    individual_net = int(investor_latest.get('개인', 0) / price) if price > 0 else 0
                else:
                    foreign_net = 0
                    institution_net = 0
                    individual_net = 0

            except Exception as e:
                print(f"⚠️  투자자 매매 동향 조회 오류: {e}")
                foreign_net = 0
                institution_net = 0
                individual_net = 0

            market_data = MarketData(
                ticker=ticker,
                timestamp=datetime.now().isoformat(),
                price=float(latest['종가']),
                open=float(latest['시가']),
                high=float(latest['고가']),
                low=float(latest['저가']),
                volume=int(latest['거래량']),
                foreign_buy=max(0, foreign_net),
                foreign_sell=max(0, -foreign_net),
                institution_buy=max(0, institution_net),
                institution_sell=max(0, -institution_net),
                individual_buy=max(0, individual_net),
                individual_sell=max(0, -individual_net),
                program_buy=0,
                program_sell=0,
                short_sell_volume=0
            )

            # 캐시 저장
            self.price_cache[ticker] = (datetime.now(), market_data)
            return market_data

        except Exception as e:
            print(f"⚠️  KRX 시세 조회 오류 ({ticker}): {e}")
            print(f"   CSV 파일 폴백 시도 중...")
            return self._load_from_csv(ticker)

    def get_market_data_batch(self, tickers: List[str]) -> Dict[str, MarketData]:
        """여러 종목 시세 일괄 조회"""
        result = {}
        print(f"📊 {len(tickers)}개 종목 KRX 시세 조회 중...")

        for ticker in tickers:
            market_data = self.get_market_data(ticker)
            if market_data:
                result[ticker] = market_data
                print(f"  ✅ {ticker}: {market_data.price:,.0f}원")
            else:
                print(f"  ⚠️  {ticker}: 조회 실패")

        return result

    def get_account_balance(self) -> Dict:
        """계좌 잔고 조회 (포지션 파일 기반)"""
        if not self.positions or 'holdings' not in self.positions:
            return {
                'cash_balance': 0,
                'stock_value': 0,
                'total_value': 0,
                'profit_loss': 0,
                'profit_loss_pct': 0
            }

        cash_balance = self.positions.get('cash', 0)
        stock_value = 0
        total_cost = 0

        holdings = self.positions.get('holdings', {})

        for ticker, position in holdings.items():
            market_data = self.get_market_data(ticker)

            if market_data:
                current_price = market_data.price
            else:
                current_price = position.get('avg_price', 0)

            quantity = position.get('quantity', 0)
            avg_price = position.get('avg_price', 0)

            stock_value += current_price * quantity
            total_cost += avg_price * quantity

        total_value = cash_balance + stock_value
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
        """보유 종목 조회 (포지션 파일 기반)"""
        holdings = {}
        position_holdings = self.positions.get('holdings', {})

        for ticker, position in position_holdings.items():
            market_data = self.get_market_data(ticker)

            if market_data:
                current_price = market_data.price
            else:
                current_price = position.get('avg_price', 0)

            quantity = position.get('quantity', 0)
            avg_price = position.get('avg_price', 0)

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
        """주문 실행 (수동 매매이므로 추천만 출력)"""
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

    def cancel_order(self, order_id: str) -> bool:
        """주문 취소 (수동 매매이므로 지원하지 않음)"""
        print("⚠️  수동 매매 시스템은 주문 취소를 지원하지 않습니다.")
        return False

    def get_investor_flow(self, ticker: str, days: int = 20) -> Dict:
        """
        투자자별 매매 동향 조회 (기간 합산)

        Args:
            ticker: 종목코드
            days: 조회 일수

        Returns:
            투자자별 매매 동향
        """
        if not self.pykrx_available:
            return {}

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            end_str = end_date.strftime("%Y%m%d")
            start_str = start_date.strftime("%Y%m%d")

            df = self.stock.get_market_trading_value_by_date(start_str, end_str, ticker)

            if df.empty:
                return {}

            # 전체 기간 합산
            foreign_total = df['외국인합계'].sum()
            institution_total = df['기관합계'].sum()
            individual_total = df['개인'].sum()

            return {
                'foreign_net': foreign_total,
                'institution_net': institution_total,
                'individual_net': individual_total,
                'days': days
            }

        except Exception as e:
            print(f"투자자 매매 동향 조회 오류: {e}")
            return {}

    def update_position_file(self, positions: Dict):
        """포지션 파일 업데이트"""
        self.positions = positions

        try:
            with open(self.position_file, 'w', encoding='utf-8') as f:
                json.dump(positions, f, ensure_ascii=False, indent=2)
            print(f"✅ 포지션 파일 업데이트 완료: {self.position_file}")
        except Exception as e:
            print(f"❌ 포지션 파일 업데이트 실패: {e}")

    def save_positions(self):
        """현재 포지션을 파일에 저장"""
        self.update_position_file(self.positions)

    def get_ticker_name(self, ticker: str) -> str:
        """
        종목코드로 종목명 조회

        Args:
            ticker: 종목코드

        Returns:
            종목명
        """
        if not self.pykrx_available:
            return ticker

        try:
            return self.stock.get_market_ticker_name(ticker)
        except Exception:
            return ticker

    def _load_from_csv(self, ticker: str) -> Optional[MarketData]:
        """
        CSV 파일에서 시세 데이터 로드 (폴백)

        Args:
            ticker: 종목코드

        Returns:
            시장 데이터
        """
        import csv

        csv_file = f"data/market_data/{ticker}.csv"

        if not os.path.exists(csv_file):
            print(f"   ❌ CSV 파일 없음: {csv_file}")
            return None

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                if not rows:
                    print(f"   ❌ CSV 파일이 비어있음: {csv_file}")
                    return None

                # 최신 데이터 (마지막 행)
                latest = rows[-1]

                market_data = MarketData(
                    ticker=ticker,
                    timestamp=latest.get('Date', datetime.now().strftime('%Y-%m-%d')),
                    price=float(latest['Close']),
                    open=float(latest['Open']),
                    high=float(latest['High']),
                    low=float(latest['Low']),
                    volume=int(latest['Volume']),
                    foreign_buy=0,
                    foreign_sell=0,
                    institution_buy=0,
                    institution_sell=0,
                    individual_buy=0,
                    individual_sell=0,
                    program_buy=0,
                    program_sell=0,
                    short_sell_volume=0
                )

                # 캐시 저장
                self.price_cache[ticker] = (datetime.now(), market_data)

                print(f"   ✅ CSV에서 로드: {ticker} = {market_data.price:,.0f}원")
                return market_data

        except Exception as e:
            print(f"   ❌ CSV 로드 실패: {e}")
            return None
