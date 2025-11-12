"""
데이터 로딩 유틸리티
"""
import json
from typing import List
from ..models.stock import Stock


class DataLoader:
    """
    주식 데이터 로딩 클래스
    """

    @staticmethod
    def load_from_json(file_path: str) -> List[Stock]:
        """
        JSON 파일에서 주식 데이터 로드

        Args:
            file_path: JSON 파일 경로

        Returns:
            Stock 객체 리스트
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        stocks = []
        for stock_data in data:
            stock = Stock(
                ticker=stock_data['ticker'],
                name=stock_data['name'],
                sector=stock_data['sector'],
                price=stock_data['price'],
                historical_returns=stock_data['historical_returns'],
                trading_volume=stock_data['trading_volume'],
                market_cap=stock_data['market_cap'],
                debt_to_equity=stock_data.get('debt_to_equity', 0.0),
                current_ratio=stock_data.get('current_ratio', 1.0),
                credit_rating=stock_data.get('credit_rating', None)
            )
            stocks.append(stock)

        return stocks

    @staticmethod
    def save_to_json(stocks: List[Stock], file_path: str):
        """
        주식 데이터를 JSON 파일로 저장

        Args:
            stocks: Stock 객체 리스트
            file_path: 저장할 JSON 파일 경로
        """
        data = []
        for stock in stocks:
            stock_data = {
                'ticker': stock.ticker,
                'name': stock.name,
                'sector': stock.sector,
                'price': stock.price,
                'historical_returns': stock.historical_returns.tolist(),
                'trading_volume': stock.trading_volume,
                'market_cap': stock.market_cap,
                'debt_to_equity': stock.debt_to_equity,
                'current_ratio': stock.current_ratio,
                'credit_rating': stock.credit_rating
            }
            data.append(stock_data)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
