"""
KRX (한국거래소) API 클라이언트
로컬 CSV 파일 또는 FinanceDataReader를 사용하여 시장 데이터를 가져옵니다
"""
import json
import os
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .base_client import BaseAPIClient, MarketData, OrderRequest, OrderResponse


class KRXAPIClient(BaseAPIClient):
    """
    KRX API 클라이언트
    - 로컬 CSV 파일 우선 사용
    - FinanceDataReader 대체 사용
    - 포지션은 파일로 관리 (수동 매매)
    """

    def __init__(
        self,
        position_file: str = "data/my_positions.json",
        dart_api_key: Optional[str] = None,
        data_dir: str = "data/market_data"
    ):
        """
        Args:
            position_file: 포지션 정보 파일 경로
            dart_api_key: DART API 키 (선택사항)
            data_dir: 시세 데이터 CSV 디렉토리
        """
        self.position_file = position_file
        self.dart_api_key = dart_api_key or self._load_env_variable('DART_API_KEY')
        self.data_dir = data_dir
        self.positions = {}
        self.is_connected = False

        # CSV 데이터 캐시
        self.price_cache = {}

        # FinanceDataReader (선택사항)
        try:
            import FinanceDataReader as fdr
            self.fdr = fdr
            self.fdr_available = True
        except ImportError:
            self.fdr = None
            self.fdr_available = False

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

        # 데이터 디렉토리 생성
        os.makedirs(self.data_dir, exist_ok=True)

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
        print("✅ 연결 완료")

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

    def _load_csv_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """로컬 CSV 파일에서 데이터 로드"""
        csv_file = os.path.join(self.data_dir, f"{ticker}.csv")

        if not os.path.exists(csv_file):
            return None

        try:
            df = pd.read_csv(csv_file, parse_dates=['Date'], index_col='Date')
            return df
        except Exception as e:
            print(f"⚠️  CSV 파일 읽기 오류 ({ticker}): {e}")
            return None

    def _get_latest_price_from_csv(self, ticker: str) -> Optional[Dict]:
        """CSV에서 최신 시세 조회"""
        df = self._load_csv_data(ticker)

        if df is None or df.empty:
            return None

        latest = df.iloc[-1]

        return {
            'close': float(latest.get('Close', latest.get('close', 0))),
            'volume': int(latest.get('Volume', latest.get('volume', 0))),
            'date': df.index[-1]
        }

    def get_market_data(self, ticker: str) -> Optional[MarketData]:
        """
        시세 조회 (CSV 우선, FinanceDataReader 대체)

        Args:
            ticker: 종목코드

        Returns:
            시장 데이터
        """
        # 캐시 확인
        if ticker in self.price_cache:
            cache_time, data = self.price_cache[ticker]
            # 5분 이내 캐시는 재사용
            if (datetime.now() - cache_time).seconds < 300:
                return data

        # 1. CSV 파일에서 조회
        csv_data = self._get_latest_price_from_csv(ticker)

        if csv_data:
            market_data = MarketData(
                ticker=ticker,
                timestamp=datetime.now().isoformat(),
                price=csv_data['close'],
                open=csv_data['close'],  # CSV에 없으면 종가로 대체
                high=csv_data['close'],
                low=csv_data['close'],
                volume=csv_data['volume'],
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
            return market_data

        # 2. FinanceDataReader 시도
        if self.fdr_available:
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=40)

                df = self.fdr.DataReader(ticker, start_date, end_date)

                if not df.empty:
                    latest = df.iloc[-1]

                    market_data = MarketData(
                        ticker=ticker,
                        timestamp=datetime.now().isoformat(),
                        price=float(latest['Close']),
                        open=float(latest.get('Open', latest['Close'])),
                        high=float(latest.get('High', latest['Close'])),
                        low=float(latest.get('Low', latest['Close'])),
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
                    return market_data

            except Exception as e:
                print(f"⚠️  FinanceDataReader 조회 오류 ({ticker}): {e}")

        print(f"⚠️  {ticker}: 시세를 조회할 수 없습니다 (CSV 파일 또는 API 데이터 필요)")
        return None

    def get_market_data_batch(self, tickers: List[str]) -> Dict[str, MarketData]:
        """여러 종목 시세 일괄 조회"""
        result = {}
        print(f"📊 {len(tickers)}개 종목 시세 조회 중...")

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
        """투자자별 매매 동향 조회 (현재 미지원)"""
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

    def download_and_save_data(self, ticker: str, start_date: str = '2024-01-01', end_date: str = '2024-12-31'):
        """
        FinanceDataReader로 데이터 다운로드하여 CSV로 저장

        Args:
            ticker: 종목코드
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
        """
        if not self.fdr_available:
            print("❌ FinanceDataReader가 설치되지 않았습니다.")
            return False

        try:
            print(f"📥 {ticker} 데이터 다운로드 중...")

            df = self.fdr.DataReader(ticker, start_date, end_date)

            if df.empty:
                print(f"❌ {ticker}: 데이터를 가져올 수 없습니다")
                return False

            # CSV로 저장
            csv_file = os.path.join(self.data_dir, f"{ticker}.csv")
            df.to_csv(csv_file)

            print(f"✅ {ticker}: {len(df)}개 데이터 저장 완료 ({csv_file})")
            return True

        except Exception as e:
            print(f"❌ {ticker} 다운로드 오류: {e}")
            return False
