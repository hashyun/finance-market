"""
KRX (한국거래소) 및 DART API 클라이언트
KRX와 DART의 공식 API를 직접 사용하여 시장 데이터를 가져옵니다
"""
import json
import os
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .base_client import BaseAPIClient, MarketData, OrderRequest, OrderResponse


class KRXAPIClient(BaseAPIClient):
    """
    KRX & DART API 클라이언트
    - KRX 정보데이터시스템에서 시세 및 투자자 매매 동향 조회
    - DART에서 기업 정보 조회
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
            dart_api_key: DART API 키 (선택사항, 없으면 환경변수에서 읽음)
        """
        self.position_file = position_file

        # DART API 키: 파라미터 > 환경변수 순서로 확인
        self.dart_api_key = dart_api_key or self._load_env_variable('DART_API_KEY')

        self.positions = {}
        self.is_connected = False

        # KRX API 엔드포인트
        self.krx_base_url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"

        # DART API 엔드포인트
        self.dart_base_url = "https://opendart.fss.or.kr/api"

        # 세션 생성 (헤더 설정)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://data.krx.co.kr/'
        })

    def _load_env_variable(self, key: str) -> Optional[str]:
        """
        환경변수 또는 .env 파일에서 값 읽기

        Args:
            key: 환경변수 이름

        Returns:
            환경변수 값 또는 None
        """
        # 1. 환경변수 확인
        value = os.environ.get(key)
        if value:
            return value

        # 2. .env 파일 확인
        env_file = '.env'
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        # 주석이나 빈 줄 스킵
                        if not line or line.startswith('#'):
                            continue

                        # KEY=VALUE 형식 파싱
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

        if not self.dart_api_key:
            print("ℹ️  DART API 키가 설정되지 않았습니다. (선택사항)")
            print("   발급: https://opendart.fss.or.kr/")

    def disconnect(self):
        """연결 해제"""
        self.session.close()
        self.is_connected = False
        print("연결 해제")

    def is_market_open(self) -> bool:
        """장 운영 시간 확인"""
        now = datetime.now()

        # 주말 제외
        if now.weekday() >= 5:
            return False

        # 평일 9:00 ~ 15:30
        market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

        return market_open <= now <= market_close

    def _get_krx_stock_price(self, ticker: str, date_str: str) -> Optional[Dict]:
        """
        KRX에서 개별 종목 시세 조회

        Args:
            ticker: 종목코드
            date_str: 날짜 (YYYYMMDD)

        Returns:
            시세 데이터
        """
        try:
            # KRX 개별종목 시세 조회 API
            params = {
                'bld': 'dbms/MDC/STAT/standard/MDCSTAT01501',
                'isuCd': ticker,
                'isuCd2': ticker,
                'strtDd': date_str,
                'endDd': date_str,
                'share': '1',
                'money': '1',
                'csvxls_isNo': 'false'
            }

            response = self.session.get(self.krx_base_url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if 'output' in data and len(data['output']) > 0:
                    result = data['output'][0]
                    return {
                        'date': result.get('TRD_DD'),
                        'close': int(result.get('TDD_CLSPRC', '0').replace(',', '')),
                        'open': int(result.get('TDD_OPNPRC', '0').replace(',', '')),
                        'high': int(result.get('TDD_HGPRC', '0').replace(',', '')),
                        'low': int(result.get('TDD_LWPRC', '0').replace(',', '')),
                        'volume': int(result.get('ACC_TRDVOL', '0').replace(',', ''))
                    }

            return None

        except Exception as e:
            print(f"⚠️  KRX 시세 조회 오류 ({ticker}): {e}")
            return None

    def _get_krx_investor_trading(self, ticker: str, date_str: str) -> Optional[Dict]:
        """
        KRX에서 투자자별 매매 동향 조회

        Args:
            ticker: 종목코드
            date_str: 날짜 (YYYYMMDD)

        Returns:
            투자자별 매매 데이터
        """
        try:
            # KRX 투자자별 매매동향 API
            params = {
                'bld': 'dbms/MDC/STAT/standard/MDCSTAT02203',
                'isuCd': ticker,
                'strtDd': date_str,
                'endDd': date_str,
                'askBid': '1',  # 1: 순매수
                'inqTpCd': '1',
                'csvxls_isNo': 'false'
            }

            response = self.session.get(self.krx_base_url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if 'output' in data and len(data['output']) > 0:
                    result = data['output'][0]

                    return {
                        'foreign_net': int(result.get('FRGN_B', '0').replace(',', '')),
                        'institution_net': int(result.get('ORG_B', '0').replace(',', '')),
                        'individual_net': int(result.get('INDV_B', '0').replace(',', ''))
                    }

            return None

        except Exception as e:
            print(f"⚠️  KRX 투자자 매매 조회 오류: {e}")
            return None

    def get_market_data(self, ticker: str) -> Optional[MarketData]:
        """
        실시간 시세 조회 (KRX API 사용)

        Args:
            ticker: 종목코드

        Returns:
            시장 데이터
        """
        try:
            # 최근 거래일 찾기 (최대 10일 전까지)
            for i in range(10):
                date_obj = datetime.now() - timedelta(days=i)
                date_str = date_obj.strftime("%Y%m%d")

                # 주말 제외
                if date_obj.weekday() >= 5:
                    continue

                # 시세 조회
                price_data = self._get_krx_stock_price(ticker, date_str)

                if price_data:
                    # 투자자별 매매 동향 조회
                    investor_data = self._get_krx_investor_trading(ticker, date_str)

                    if not investor_data:
                        investor_data = {
                            'foreign_net': 0,
                            'institution_net': 0,
                            'individual_net': 0
                        }

                    return MarketData(
                        ticker=ticker,
                        timestamp=datetime.now().isoformat(),
                        price=float(price_data['close']),
                        volume=int(price_data['volume']),
                        foreign_buy=max(0, investor_data['foreign_net']),
                        foreign_sell=max(0, -investor_data['foreign_net']),
                        foreign_net=investor_data['foreign_net'],
                        institution_buy=max(0, investor_data['institution_net']),
                        institution_sell=max(0, -investor_data['institution_net']),
                        institution_net=investor_data['institution_net'],
                        individual_buy=max(0, investor_data['individual_net']),
                        individual_sell=max(0, -investor_data['individual_net']),
                        individual_net=investor_data['individual_net'],
                        program_buy=0,
                        program_sell=0,
                        program_net=0
                    )

            print(f"⚠️  {ticker}: 최근 거래 데이터를 찾을 수 없습니다")
            return None

        except Exception as e:
            print(f"❌ 시세 조회 오류 ({ticker}): {e}")
            return None

    def get_market_data_batch(self, tickers: List[str]) -> Dict[str, MarketData]:
        """
        여러 종목 시세 일괄 조회

        Args:
            tickers: 종목코드 리스트

        Returns:
            {ticker: MarketData} 딕셔너리
        """
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
        """
        계좌 잔고 조회 (포지션 파일 기반)

        Returns:
            계좌 정보
        """
        if not self.positions or 'holdings' not in self.positions:
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
                current_price = position.get('avg_price', 0)

            quantity = position.get('quantity', 0)
            avg_price = position.get('avg_price', 0)

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

    def cancel_order(self, order_id: str) -> bool:
        """
        주문 취소 (수동 매매이므로 지원하지 않음)

        Args:
            order_id: 주문 ID

        Returns:
            False (지원하지 않음)
        """
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
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            start_str = start_date.strftime("%Y%m%d")
            end_str = end_date.strftime("%Y%m%d")

            # KRX 투자자별 매매동향 기간 조회
            params = {
                'bld': 'dbms/MDC/STAT/standard/MDCSTAT02203',
                'isuCd': ticker,
                'strtDd': start_str,
                'endDd': end_str,
                'askBid': '1',
                'inqTpCd': '1',
                'csvxls_isNo': 'false'
            }

            response = self.session.get(self.krx_base_url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if 'output' in data and len(data['output']) > 0:
                    # 전체 기간 합산
                    foreign_total = sum(
                        int(row.get('FRGN_B', '0').replace(',', ''))
                        for row in data['output']
                    )
                    institution_total = sum(
                        int(row.get('ORG_B', '0').replace(',', ''))
                        for row in data['output']
                    )
                    individual_total = sum(
                        int(row.get('INDV_B', '0').replace(',', ''))
                        for row in data['output']
                    )

                    return {
                        'foreign_net': foreign_total,
                        'institution_net': institution_total,
                        'individual_net': individual_total,
                        'days': days
                    }

            return {}

        except Exception as e:
            print(f"투자자 매매 동향 조회 오류: {e}")
            return {}

    def get_company_info_from_dart(self, corp_code: str) -> Optional[Dict]:
        """
        DART에서 기업 정보 조회 (선택사항)

        Args:
            corp_code: 기업 고유번호

        Returns:
            기업 정보
        """
        if not self.dart_api_key:
            return None

        try:
            url = f"{self.dart_base_url}/company.json"
            params = {
                'crtfc_key': self.dart_api_key,
                'corp_code': corp_code
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()

            return None

        except Exception as e:
            print(f"DART 기업 정보 조회 오류: {e}")
            return None

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
            print(f"✅ 포지션 파일 업데이트 완료: {self.position_file}")
        except Exception as e:
            print(f"❌ 포지션 파일 업데이트 실패: {e}")

    def save_positions(self):
        """현재 포지션을 파일에 저장"""
        self.update_position_file(self.positions)
