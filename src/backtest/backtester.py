"""
백테스팅 엔진
"""
import numpy as np
from typing import List, Dict
from dataclasses import dataclass
from ..models.korean_stock import KoreanStock
from ..strategies.base_strategy import BaseStrategy, TradingSignal


@dataclass
class Trade:
    """거래 기록"""
    date: str
    ticker: str
    action: str  # "BUY" or "SELL"
    price: float
    shares: int
    amount: float


@dataclass
class BacktestResult:
    """백테스트 결과"""
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    num_trades: int
    num_wins: int
    num_losses: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    trades: List[Trade]
    daily_values: List[float]
    daily_returns: List[float]


class Backtester:
    """
    백테스팅 엔진
    """

    def __init__(
        self,
        initial_capital: float = 100_000_000,  # 1억원
        commission_rate: float = 0.00015,  # 수수료 0.015%
        tax_rate: float = 0.0023,  # 증권거래세 0.23%
        max_position_size: float = 0.3  # 최대 포지션 크기 (30%)
    ):
        """
        Args:
            initial_capital: 초기 자본
            commission_rate: 수수료율
            tax_rate: 세금율 (매도 시)
            max_position_size: 단일 종목 최대 비중
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.tax_rate = tax_rate
        self.max_position_size = max_position_size

    def run(
        self,
        stocks: List[KoreanStock],
        strategy: BaseStrategy,
        start_date: str = None,
        end_date: str = None,
        rebalance_period: int = 5  # 리밸런싱 주기 (일)
    ) -> BacktestResult:
        """
        백테스트 실행

        Args:
            stocks: 주식 리스트
            strategy: 트레이딩 전략
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            rebalance_period: 리밸런싱 주기

        Returns:
            백테스트 결과
        """
        # 날짜 범위 설정
        all_dates = sorted(set(
            td.date for stock in stocks for td in stock.trading_data
        ))

        if start_date:
            all_dates = [d for d in all_dates if d >= start_date]
        if end_date:
            all_dates = [d for d in all_dates if d <= end_date]

        if not all_dates:
            return self._empty_result()

        # 초기화
        cash = self.initial_capital
        positions = {}  # {ticker: shares}
        trades = []
        daily_values = []
        daily_returns = []

        # 백테스트 실행
        for day_idx, date in enumerate(all_dates):
            # 리밸런싱 시점 확인
            if day_idx % rebalance_period == 0:
                # 신호 생성
                signals = self._generate_signals(stocks, strategy, date)

                # 매도 먼저 실행
                for ticker, signal in signals.items():
                    if signal == TradingSignal.SELL and ticker in positions:
                        trade = self._execute_trade(
                            ticker, TradingSignal.SELL,
                            positions[ticker], stocks, date,
                            cash, positions
                        )
                        if trade:
                            trades.append(trade)
                            cash = trade.amount
                            del positions[ticker]

                # 매수 실행
                buy_signals = {
                    ticker: signal for ticker, signal in signals.items()
                    if signal == TradingSignal.BUY
                }

                if buy_signals:
                    # 매수할 종목별로 자본 배분
                    capital_per_stock = min(
                        cash / len(buy_signals),
                        self.initial_capital * self.max_position_size
                    )

                    for ticker in buy_signals:
                        trade = self._execute_trade(
                            ticker, TradingSignal.BUY,
                            capital_per_stock, stocks, date,
                            cash, positions
                        )
                        if trade:
                            trades.append(trade)
                            cash -= trade.amount

            # 일일 자산 가치 계산
            portfolio_value = self._calculate_portfolio_value(
                cash, positions, stocks, date
            )
            daily_values.append(portfolio_value)

            # 일일 수익률
            if len(daily_values) > 1:
                daily_return = (daily_values[-1] - daily_values[-2]) / daily_values[-2]
                daily_returns.append(daily_return)

        # 결과 계산
        result = self._calculate_result(
            self.initial_capital,
            daily_values[-1] if daily_values else self.initial_capital,
            trades,
            daily_values,
            daily_returns
        )

        return result

    def _generate_signals(
        self,
        stocks: List[KoreanStock],
        strategy: BaseStrategy,
        current_date: str
    ) -> Dict[str, str]:
        """특정 날짜의 매매 신호 생성"""
        signals = {}

        for stock in stocks:
            # 현재 날짜까지의 데이터만 사용
            historical_data = [
                td for td in stock.trading_data
                if td.date <= current_date
            ]

            if len(historical_data) < 20:  # 최소 데이터 요구
                continue

            # 임시 주식 객체 생성 (과거 데이터만 포함)
            temp_stock = KoreanStock(
                ticker=stock.ticker,
                name=stock.name,
                sector=stock.sector,
                market=stock.market,
                trading_data=historical_data,
                market_cap=stock.market_cap,
                debt_to_equity=stock.debt_to_equity,
                current_ratio=stock.current_ratio,
                credit_rating=stock.credit_rating
            )

            try:
                signal = strategy.generate_signal(temp_stock)
                signals[stock.ticker] = signal
            except Exception as e:
                continue

        return signals

    def _execute_trade(
        self,
        ticker: str,
        action: str,
        amount_or_shares: float,
        stocks: List[KoreanStock],
        date: str,
        cash: float,
        positions: Dict
    ) -> Trade:
        """거래 실행"""
        # 주식 찾기
        stock = next((s for s in stocks if s.ticker == ticker), None)
        if not stock:
            return None

        # 해당 날짜의 가격 찾기
        price_data = next((td for td in stock.trading_data if td.date == date), None)
        if not price_data:
            return None

        price = price_data.close

        if action == TradingSignal.BUY:
            # 매수
            max_shares = int(amount_or_shares / price)
            commission = amount_or_shares * self.commission_rate
            actual_amount = amount_or_shares + commission

            if actual_amount > cash:
                return None

            if ticker in positions:
                positions[ticker] += max_shares
            else:
                positions[ticker] = max_shares

            return Trade(
                date=date,
                ticker=ticker,
                action="BUY",
                price=price,
                shares=max_shares,
                amount=actual_amount
            )

        elif action == TradingSignal.SELL:
            # 매도
            shares = amount_or_shares
            if ticker not in positions or positions[ticker] < shares:
                return None

            gross_amount = shares * price
            commission = gross_amount * self.commission_rate
            tax = gross_amount * self.tax_rate
            net_amount = gross_amount - commission - tax

            return Trade(
                date=date,
                ticker=ticker,
                action="SELL",
                price=price,
                shares=shares,
                amount=cash + net_amount
            )

        return None

    def _calculate_portfolio_value(
        self,
        cash: float,
        positions: Dict,
        stocks: List[KoreanStock],
        date: str
    ) -> float:
        """포트폴리오 총 가치 계산"""
        total_value = cash

        for ticker, shares in positions.items():
            stock = next((s for s in stocks if s.ticker == ticker), None)
            if stock:
                price_data = next((td for td in stock.trading_data if td.date == date), None)
                if price_data:
                    total_value += shares * price_data.close

        return total_value

    def _calculate_result(
        self,
        initial_capital: float,
        final_capital: float,
        trades: List[Trade],
        daily_values: List[float],
        daily_returns: List[float]
    ) -> BacktestResult:
        """백테스트 결과 계산"""
        # 수익률
        total_return = final_capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100

        # 승률 계산
        buy_trades = [t for t in trades if t.action == "BUY"]
        sell_trades = [t for t in trades if t.action == "SELL"]

        wins = 0
        losses = 0

        # 매수-매도 쌍으로 승패 계산
        buy_dict = {}
        for trade in buy_trades:
            if trade.ticker not in buy_dict:
                buy_dict[trade.ticker] = []
            buy_dict[trade.ticker].append(trade)

        for trade in sell_trades:
            if trade.ticker in buy_dict and buy_dict[trade.ticker]:
                buy_trade = buy_dict[trade.ticker].pop(0)
                profit = (trade.price - buy_trade.price) * trade.shares
                if profit > 0:
                    wins += 1
                else:
                    losses += 1

        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

        # 최대 낙폭
        max_drawdown = 0
        if daily_values:
            peak = daily_values[0]
            for value in daily_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

        # 샤프 비율
        if daily_returns:
            avg_return = np.mean(daily_returns)
            std_return = np.std(daily_returns)
            sharpe_ratio = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        else:
            sharpe_ratio = 0

        return BacktestResult(
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_pct=total_return_pct,
            num_trades=len(trades),
            num_wins=wins,
            num_losses=losses,
            win_rate=win_rate,
            max_drawdown=max_drawdown * 100,
            sharpe_ratio=sharpe_ratio,
            trades=trades,
            daily_values=daily_values,
            daily_returns=daily_returns
        )

    def _empty_result(self) -> BacktestResult:
        """빈 결과 반환"""
        return BacktestResult(
            initial_capital=self.initial_capital,
            final_capital=self.initial_capital,
            total_return=0,
            total_return_pct=0,
            num_trades=0,
            num_wins=0,
            num_losses=0,
            win_rate=0,
            max_drawdown=0,
            sharpe_ratio=0,
            trades=[],
            daily_values=[],
            daily_returns=[]
        )
