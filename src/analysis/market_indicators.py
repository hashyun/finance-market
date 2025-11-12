"""
한국 시장 특화 기술적 지표
"""
import numpy as np
from typing import List, Optional
from ..models.korean_stock import KoreanStock


class KoreanMarketIndicators:
    """
    한국 시장 특화 기술적 지표 계산
    """

    @staticmethod
    def moving_average(prices: np.ndarray, window: int) -> np.ndarray:
        """이동평균"""
        if len(prices) < window:
            return np.array([])
        return np.convolve(prices, np.ones(window)/window, mode='valid')

    @staticmethod
    def rsi(prices: np.ndarray, period: int = 14) -> float:
        """
        RSI (Relative Strength Index)

        Returns:
            RSI 값 (0 ~ 100)
        """
        if len(prices) < period + 1:
            return 50.0

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def macd(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
        """
        MACD (Moving Average Convergence Divergence)

        Returns:
            MACD, Signal, Histogram
        """
        if len(prices) < slow + signal:
            return {'macd': 0, 'signal': 0, 'histogram': 0}

        # EMA 계산
        def ema(data, period):
            weights = np.exp(np.linspace(-1., 0., period))
            weights /= weights.sum()

            ema_values = np.convolve(data, weights, mode='valid')
            return ema_values[-1] if len(ema_values) > 0 else 0

        fast_ema = ema(prices, fast)
        slow_ema = ema(prices, slow)

        macd_line = fast_ema - slow_ema

        # Signal line은 MACD의 EMA
        # 간단히 최근 9일 평균으로 계산
        if len(prices) >= slow + signal:
            recent_macd = []
            for i in range(signal):
                idx = len(prices) - signal + i
                if idx >= slow:
                    f_ema = ema(prices[:idx+1], fast)
                    s_ema = ema(prices[:idx+1], slow)
                    recent_macd.append(f_ema - s_ema)

            signal_line = np.mean(recent_macd) if recent_macd else macd_line
        else:
            signal_line = macd_line

        histogram = macd_line - signal_line

        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

    @staticmethod
    def bollinger_bands(prices: np.ndarray, window: int = 20, num_std: float = 2.0) -> dict:
        """
        볼린저 밴드

        Returns:
            상단밴드, 중간밴드(이동평균), 하단밴드
        """
        if len(prices) < window:
            current_price = prices[-1] if len(prices) > 0 else 0
            return {
                'upper': current_price,
                'middle': current_price,
                'lower': current_price
            }

        recent_prices = prices[-window:]
        middle = np.mean(recent_prices)
        std = np.std(recent_prices)

        upper = middle + (std * num_std)
        lower = middle - (std * num_std)

        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }

    @staticmethod
    def stochastic(stock: KoreanStock, k_period: int = 14, d_period: int = 3) -> dict:
        """
        스토캐스틱 오실레이터

        Returns:
            %K, %D
        """
        if len(stock.trading_data) < k_period:
            return {'k': 50, 'd': 50}

        recent_data = stock.trading_data[-k_period:]

        current_close = recent_data[-1].close
        highest_high = max(td.high for td in recent_data)
        lowest_low = min(td.low for td in recent_data)

        if highest_high == lowest_low:
            k = 50
        else:
            k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100

        # %D는 %K의 이동평균
        if len(stock.trading_data) >= k_period + d_period:
            k_values = []
            for i in range(d_period):
                idx = -d_period + i
                data_slice = stock.trading_data[idx-k_period:idx+1] if idx != 0 else stock.trading_data[-k_period:]

                if len(data_slice) >= k_period:
                    close = data_slice[-1].close
                    high = max(td.high for td in data_slice)
                    low = min(td.low for td in data_slice)

                    if high != low:
                        k_values.append(((close - low) / (high - low)) * 100)
                    else:
                        k_values.append(50)

            d = np.mean(k_values) if k_values else k
        else:
            d = k

        return {'k': k, 'd': d}

    @staticmethod
    def atr(stock: KoreanStock, period: int = 14) -> float:
        """
        ATR (Average True Range) - 변동성 지표

        Returns:
            ATR 값
        """
        if len(stock.trading_data) < period + 1:
            return 0.0

        recent_data = stock.trading_data[-period-1:]

        true_ranges = []
        for i in range(1, len(recent_data)):
            high = recent_data[i].high
            low = recent_data[i].low
            prev_close = recent_data[i-1].close

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)

        atr = np.mean(true_ranges)
        return atr

    @staticmethod
    def obv(stock: KoreanStock) -> float:
        """
        OBV (On-Balance Volume) - 거래량 기반 지표

        Returns:
            OBV 값
        """
        if len(stock.trading_data) < 2:
            return 0.0

        obv_value = 0
        for i in range(1, len(stock.trading_data)):
            if stock.trading_data[i].close > stock.trading_data[i-1].close:
                obv_value += stock.trading_data[i].volume
            elif stock.trading_data[i].close < stock.trading_data[i-1].close:
                obv_value -= stock.trading_data[i].volume

        return obv_value

    @staticmethod
    def calculate_all_indicators(stock: KoreanStock) -> dict:
        """
        모든 기술적 지표 계산

        Returns:
            모든 지표를 포함한 딕셔너리
        """
        prices = stock.get_price_data()

        if len(prices) < 2:
            return {}

        # 현재가
        current_price = prices[-1]

        # 이동평균
        ma5 = KoreanMarketIndicators.moving_average(prices, 5)
        ma20 = KoreanMarketIndicators.moving_average(prices, 20)
        ma60 = KoreanMarketIndicators.moving_average(prices, 60)

        # RSI
        rsi = KoreanMarketIndicators.rsi(prices)

        # MACD
        macd_data = KoreanMarketIndicators.macd(prices)

        # 볼린저 밴드
        bb = KoreanMarketIndicators.bollinger_bands(prices)

        # 스토캐스틱
        stoch = KoreanMarketIndicators.stochastic(stock)

        # ATR
        atr = KoreanMarketIndicators.atr(stock)

        # OBV
        obv = KoreanMarketIndicators.obv(stock)

        # 볼린저 밴드 위치 (%)
        if bb['upper'] != bb['lower']:
            bb_position = (current_price - bb['lower']) / (bb['upper'] - bb['lower']) * 100
        else:
            bb_position = 50

        return {
            'price': current_price,
            'ma5': ma5[-1] if len(ma5) > 0 else current_price,
            'ma20': ma20[-1] if len(ma20) > 0 else current_price,
            'ma60': ma60[-1] if len(ma60) > 0 else current_price,
            'rsi': rsi,
            'macd': macd_data['macd'],
            'macd_signal': macd_data['signal'],
            'macd_histogram': macd_data['histogram'],
            'bb_upper': bb['upper'],
            'bb_middle': bb['middle'],
            'bb_lower': bb['lower'],
            'bb_position': bb_position,
            'stochastic_k': stoch['k'],
            'stochastic_d': stoch['d'],
            'atr': atr,
            'obv': obv
        }
