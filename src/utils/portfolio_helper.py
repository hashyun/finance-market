"""
포트폴리오 헬퍼 유틸리티
간단한 입력으로 포트폴리오 생성 및 분석
"""
import re
from typing import List, Dict, Tuple, Optional
import numpy as np
from datetime import datetime, timedelta

try:
    from pykrx import stock
    PYKRX_AVAILABLE = True
except ImportError:
    PYKRX_AVAILABLE = False
    stock = None

from ..models.stock import Stock, Portfolio


class PortfolioHelper:
    """
    간단한 텍스트 입력으로 포트폴리오 생성
    """

    @staticmethod
    def parse_position_text(text: str) -> List[Dict[str, any]]:
        """
        자연어 입력을 파싱하여 포지션 정보 추출

        입력 예시:
        - "삼성전자 100주, SK하이닉스 50주, NAVER 30주"
        - "005930 100주, 000660 50주"
        - "삼성전자(005930) 100주"

        Returns:
            [{"ticker": "005930", "name": "삼성전자", "quantity": 100}, ...]
        """
        positions = []

        # 쉼표로 분리
        items = text.split(',')

        for item in items:
            item = item.strip()
            if not item:
                continue

            # 패턴 매칭
            # "삼성전자 100주" 또는 "005930 100주" 또는 "삼성전자(005930) 100주"
            match = re.search(r'([가-힣a-zA-Z]+)?\s*\(?(\d{6})?\)?\s*(\d+)\s*주?', item)

            if match:
                name = match.group(1)
                ticker = match.group(2)
                quantity = int(match.group(3))

                if ticker:
                    positions.append({
                        "ticker": ticker,
                        "name": name or ticker,
                        "quantity": quantity
                    })
                elif name:
                    # 이름만 있으면 종목코드 검색 필요
                    positions.append({
                        "name": name,
                        "quantity": quantity
                    })

        return positions

    @staticmethod
    def get_stock_data(ticker: str, days: int = 252) -> Optional[Dict]:
        """
        종목의 실시간 데이터 조회 (pykrx 사용)

        Args:
            ticker: 종목코드 (6자리)
            days: 과거 데이터 일수

        Returns:
            주식 데이터 딕셔너리
        """
        if not PYKRX_AVAILABLE:
            return None

        try:
            # 날짜 설정
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # 가격 데이터 조회
            df = stock.get_market_ohlcv_by_date(
                start_date.strftime("%Y%m%d"),
                end_date.strftime("%Y%m%d"),
                ticker
            )

            if df.empty:
                return None

            # 기본 정보 조회
            try:
                current_price = df['종가'].iloc[-1]
                market_cap = stock.get_market_cap_by_date(
                    end_date.strftime("%Y%m%d"),
                    end_date.strftime("%Y%m%d"),
                    ticker
                ).iloc[-1]['시가총액']

                # 종목명 조회
                name = stock.get_market_ticker_name(ticker)

                # 거래량
                trading_volume = df['거래량'].iloc[-1]

            except:
                current_price = df['종가'].iloc[-1]
                market_cap = 10000000000000  # 기본값 10조
                name = ticker
                trading_volume = df['거래량'].mean()

            # 수익률 계산
            returns = df['종가'].pct_change().dropna().values

            # 섹터 추정 (간단한 버전)
            sector = PortfolioHelper._guess_sector(name, ticker)

            return {
                "ticker": ticker,
                "name": name,
                "sector": sector,
                "price": float(current_price),
                "historical_returns": returns.tolist(),
                "trading_volume": float(trading_volume),
                "market_cap": float(market_cap),
                "debt_to_equity": 1.0,  # 기본값
                "current_ratio": 1.5,   # 기본값
                "credit_rating": "BBB"  # 기본값
            }

        except Exception as e:
            print(f"종목 {ticker} 데이터 조회 실패: {e}")
            return None

    @staticmethod
    def _guess_sector(name: str, ticker: str) -> str:
        """종목명으로 섹터 추정"""
        if any(x in name for x in ['전자', '반도체', 'SK하이닉스', '삼성전자']):
            return 'IT/전자'
        elif any(x in name for x in ['자동차', '현대차', '기아']):
            return '자동차'
        elif any(x in name for x in ['은행', '금융', '증권', '보험']):
            return '금융'
        elif any(x in name for x in ['제약', '바이오', '헬스케어']):
            return '제약/바이오'
        elif any(x in name for x in ['NAVER', '카카오', '네이버']):
            return '인터넷'
        elif any(x in name for x in ['화학', 'LG화학']):
            return '화학'
        elif any(x in name for x in ['건설', '건설', 'HD현대']):
            return '건설'
        else:
            return '기타'

    @staticmethod
    def create_portfolio_from_text(
        position_text: str,
        include_cash: bool = True
    ) -> Tuple[Portfolio, Dict]:
        """
        텍스트 입력으로 포트폴리오 생성

        Args:
            position_text: "삼성전자 100주, SK하이닉스 50주" 형식
            include_cash: 현금 비중 포함 여부

        Returns:
            (Portfolio 객체, 상세 정보 딕셔너리)
        """
        # 포지션 파싱
        positions = PortfolioHelper.parse_position_text(position_text)

        if not positions:
            raise ValueError("포지션 정보를 파싱할 수 없습니다.")

        # 주식 데이터 수집
        stocks = []
        total_value = 0
        position_details = []

        for pos in positions:
            ticker = pos.get('ticker')
            if not ticker:
                print(f"경고: {pos['name']}의 종목코드를 찾을 수 없습니다.")
                continue

            stock_data = PortfolioHelper.get_stock_data(ticker)
            if not stock_data:
                print(f"경고: {ticker} 데이터를 조회할 수 없습니다.")
                continue

            # Stock 객체 생성
            stock_obj = Stock(
                ticker=stock_data['ticker'],
                name=stock_data['name'],
                sector=stock_data['sector'],
                price=stock_data['price'],
                historical_returns=stock_data['historical_returns'],
                trading_volume=stock_data['trading_volume'],
                market_cap=stock_data['market_cap'],
                debt_to_equity=stock_data['debt_to_equity'],
                current_ratio=stock_data['current_ratio'],
                credit_rating=stock_data['credit_rating']
            )

            stocks.append(stock_obj)

            # 포지션 가치 계산
            position_value = stock_data['price'] * pos['quantity']
            total_value += position_value

            position_details.append({
                'ticker': ticker,
                'name': stock_data['name'],
                'quantity': pos['quantity'],
                'price': stock_data['price'],
                'value': position_value,
                'sector': stock_data['sector']
            })

        if not stocks:
            raise ValueError("조회 가능한 종목이 없습니다.")

        # 비중 계산
        weights = [pos['value'] / total_value for pos in position_details]

        # 포트폴리오 생성
        portfolio = Portfolio(stocks, weights)

        # 상세 정보
        details = {
            'total_value': total_value,
            'positions': position_details,
            'weights': {
                pos['ticker']: weight
                for pos, weight in zip(position_details, weights)
            }
        }

        return portfolio, details

    @staticmethod
    def format_position_summary(details: Dict) -> str:
        """포지션 요약 포맷팅"""
        lines = [
            f"💰 총 평가액: {details['total_value']:,.0f}원\n",
            "📊 보유 종목:"
        ]

        for pos in details['positions']:
            lines.append(
                f"  • {pos['name']}({pos['ticker']}): "
                f"{pos['quantity']:,}주 @ {pos['price']:,.0f}원 "
                f"= {pos['value']:,.0f}원 ({details['weights'][pos['ticker']]:.1%})"
            )

        return "\n".join(lines)
