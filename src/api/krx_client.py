"""
KRX (한국거래소) API 클라이언트
pykrx 라이브러리를 사용하여 실제 KRX 데이터를 가져옵니다
"""
import json
import os
import pandas as pd
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
                print(f"⚠️  {ticker}: 데이터가 없습니다")
                return None

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
            print(f"❌ KRX 시세 조회 오류 ({ticker}): {e}")
            return None

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

    def get_market_tickers(self, market: str = "KOSPI", date: str = None) -> List[str]:
        """
        KRX 시장의 전체 종목 리스트 조회

        Args:
            market: "KOSPI", "KOSDAQ", "KONEX", "ALL"
            date: 조회 날짜 (YYYYMMDD, None이면 오늘)

        Returns:
            종목코드 리스트
        """
        if not self.pykrx_available:
            print("❌ pykrx가 설치되지 않아 종목 리스트를 조회할 수 없습니다.")
            return []

        try:
            if date is None:
                date = datetime.now().strftime("%Y%m%d")

            tickers = self.stock.get_market_ticker_list(date, market=market)
            return list(tickers)
        except Exception as e:
            print(f"❌ 종목 리스트 조회 실패: {e}")
            return []

    def get_top_tickers_by_market_cap(
        self,
        top_n: int = 100,
        market: str = "KOSPI",
        date: str = None
    ) -> List[str]:
        """
        시가총액 상위 N개 종목 조회

        pykrx 오류 시 미리 정의된 대형주 리스트 반환

        Args:
            top_n: 상위 몇 개 종목
            market: "KOSPI", "KOSDAQ", "ALL"
            date: 조회 날짜 (YYYYMMDD, None이면 최근 거래일)

        Returns:
            종목코드 리스트 (시가총액 내림차순)
        """
        if not self.pykrx_available:
            print("❌ pykrx가 설치되지 않아 시가총액 정보를 조회할 수 없습니다.")
            return self._get_default_large_cap_tickers(market, top_n)

        try:
            if date is None:
                # 최근 거래일 사용
                date = datetime.now()
                for _ in range(30):  # 최대 30일 전까지 확인 (휴일 고려)
                    # 주말 건너뛰기
                    if date.weekday() >= 5:
                        date = date - pd.Timedelta(days=1)
                        continue

                    date_str = date.strftime("%Y%m%d")
                    try:
                        # 전체 종목 리스트로 시도 (더 안정적)
                        tickers = self.stock.get_market_ticker_list(date_str, market=market)
                        if tickers is not None and len(tickers) > 0:
                            # 종목 리스트를 리스트로 변환하고 상위 N개 반환
                            ticker_list = list(tickers)[:top_n]
                            return ticker_list
                    except Exception:
                        pass
                    date = date - pd.Timedelta(days=1)
            else:
                date_str = date
                tickers = self.stock.get_market_ticker_list(date_str, market=market)
                if tickers is not None and len(tickers) > 0:
                    return list(tickers)[:top_n]

            # 조회 실패 시 기본 대형주 리스트 사용
            print(f"⚠️  pykrx 데이터 조회 실패, 미리 정의된 대형주 리스트 사용")
            return self._get_default_large_cap_tickers(market, top_n)

        except Exception as e:
            print(f"⚠️  시가총액 상위 종목 조회 실패: {e}")
            print(f"   미리 정의된 대형주 리스트 사용")
            return self._get_default_large_cap_tickers(market, top_n)

    def _get_default_large_cap_tickers(self, market: str, top_n: int) -> List[str]:
        """
        미리 정의된 대형주 종목 리스트 (pykrx 조회 실패 시 사용)

        Args:
            market: "KOSPI", "KOSDAQ", "ALL"
            top_n: 반환할 종목 수

        Returns:
            종목코드 리스트
        """
        # KOSPI 시가총액 상위 종목 (2024년 기준)
        kospi_large_caps = [
            '005930',  # 삼성전자
            '000660',  # SK하이닉스
            '373220',  # LG에너지솔루션
            '207940',  # 삼성바이오로직스
            '005380',  # 현대차
            '006400',  # 삼성SDI
            '051910',  # LG화학
            '005490',  # POSCO홀딩스
            '035420',  # NAVER
            '068270',  # 셀트리온
            '012330',  # 현대모비스
            '028260',  # 삼성물산
            '035720',  # 카카오
            '066570',  # LG전자
            '003670',  # 포스코퓨처엠
            '055550',  # 신한지주
            '105560',  # KB금융
            '032830',  # 삼성생명
            '000270',  # 기아
            '017670',  # SK텔레콤
            '096770',  # SK이노베이션
            '034020',  # 두산에너빌리티
            '009150',  # 삼성전기
            '018260',  # 삼성에스디에스
            '086790',  # 하나금융지주
            '033780',  # KT&G
            '003550',  # LG
            '030200',  # KT
            '015760',  # 한국전력
            '010130',  # 고려아연
            '352820',  # 하이브
            '011200',  # HMM
            '000810',  # 삼성화재
            '086280',  # 현대글로비스
            '024110',  # 기업은행
            '029780',  # 삼성카드
            '000100',  # 유한양행
            '010950',  # S-Oil
            '047050',  # 포스코인터내셔널
            '011070',  # LG이노텍
            '009540',  # 현대중공업
            '004020',  # 현대제철
            '032640',  # LG유플러스
            '001570',  # 금양
            '009830',  # 한화솔루션
            '011780',  # 금호석유
            '047810',  # 한국항공우주
            '028050',  # 삼성엔지니어링
            '010140',  # 삼성중공업
            '012450',  # 한화에어로스페이스
        ]

        # KOSDAQ 시가총액 상위 종목
        kosdaq_large_caps = [
            '247540',  # 에코프로비엠
            '086520',  # 에코프로
            '091990',  # 셀트리온헬스케어
            '196170',  # 알테오젠
            '112040',  # 위메이드
            '357780',  # 솔브레인
            '214450',  # 파마리서치
            '293490',  # 카카오게임즈
            '145020',  # 휴젤
            '058470',  # 리노공업
            '039030',  # 이오테크닉스
            '278280',  # 천보
            '403870',  # HPSP
            '067160',  # 아프리카TV
            '348210',  # 넥스틴
            '365340',  # 성일하이텍
            '141080',  # 레고켐바이오
            '095340',  # ISC
            '068760',  # 셀트리온제약
            '108860',  # 셀바스AI
        ]

        if market.upper() == "KOSPI":
            return kospi_large_caps[:top_n]
        elif market.upper() == "KOSDAQ":
            return kosdaq_large_caps[:top_n]
        else:  # ALL
            combined = kospi_large_caps + kosdaq_large_caps
            return combined[:top_n]
