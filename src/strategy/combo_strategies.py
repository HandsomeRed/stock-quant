#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组合策略 - 多指标融合决策系统

提供多种指标组合方式，通过加权投票或条件叠加生成更稳健的交易信号。
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from .base import Strategy


class ComboStrategy(Strategy):
    """
    组合策略 - 多策略加权投票

    将多个子策略的信号按权重加权，超过阈值则产生买卖信号。
    """

    def __init__(
        self,
        strategies: List[Tuple[Strategy, float]],
        buy_threshold: float = 0.6,
        sell_threshold: float = -0.6,
    ):
        """
        Args:
            strategies: [(策略实例, 权重), ...] 权重之和建议为1.0
            buy_threshold: 加权信号 >= 此值触发买入
            sell_threshold: 加权信号 <= 此值触发卖出
        """
        self.strategies = strategies
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def name(self) -> str:
        names = "+".join([s.name() for s, _ in self.strategies])
        return f"Combo({names})"

    def description(self) -> str:
        parts = [f"{s.name()}(w={w})" for s, w in self.strategies]
        return f"组合策略 - {', '.join(parts)}, 买入≥{self.buy_threshold}, 卖出≤{self.sell_threshold}"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        weighted_sum = pd.Series(0.0, index=df.index)
        total_weight = sum(w for _, w in self.strategies)

        for strategy, weight in self.strategies:
            signals = strategy.generate_signals(df)
            weighted_sum += signals * (weight / total_weight)

        result = pd.Series(0, index=df.index, dtype=int)
        result[weighted_sum >= self.buy_threshold] = 1
        result[weighted_sum <= self.sell_threshold] = -1
        return result

    def get_component_signals(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """获取每个子策略的独立信号（用于分析）"""
        return {s.name(): s.generate_signals(df) for s, _ in self.strategies}


class RSIMACDCombo(Strategy):
    """
    RSI + MACD 组合策略

    买入条件：RSI 从超卖回升 AND MACD 金叉
    卖出条件：RSI 超买 OR MACD 死叉
    """

    def __init__(
        self,
        rsi_period: int = 14,
        rsi_oversold: float = 30,
        rsi_overbought: float = 70,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
    ):
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal

    def name(self) -> str:
        return f"RSI_MACD({self.rsi_period},{self.macd_fast}/{self.macd_slow})"

    def description(self) -> str:
        return f"RSI({self.rsi_period})+MACD({self.macd_fast}/{self.macd_slow}/{self.macd_signal})组合"

    def _calculate_rsi(self, prices: pd.Series) -> pd.Series:
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=self.rsi_period, min_periods=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period, min_periods=self.rsi_period).mean()
        rs = avg_gain / avg_loss.replace(0, np.inf)
        return 100 - (100 / (1 + rs))

    def _calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        ema_fast = prices.ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.macd_slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df['close'] if 'close' in df.columns else df['收盘']

        rsi = self._calculate_rsi(close)
        macd_line, signal_line, histogram = self._calculate_macd(close)

        # MACD 金叉/死叉
        macd_cross_up = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
        macd_cross_down = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))
        macd_bullish = macd_line > signal_line

        # RSI 条件
        rsi_recovering = (rsi > self.rsi_oversold) & (rsi.shift(1) <= self.rsi_oversold)
        rsi_overbought = rsi > self.rsi_overbought
        rsi_bullish = (rsi > self.rsi_oversold) & (rsi < self.rsi_overbought)

        signals = pd.Series(0, index=df.index, dtype=int)

        # 买入：RSI 从超卖回升 + MACD 看多（金叉或持续在上方）
        buy_cond = (rsi_recovering | rsi_bullish) & (macd_cross_up | macd_bullish)
        # 卖出：RSI 超买 或 MACD 死叉
        sell_cond = rsi_overbought | macd_cross_down

        signals[buy_cond] = 1
        signals[sell_cond] = -1

        return signals

    def get_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """获取中间指标（用于可视化）"""
        close = df['close'] if 'close' in df.columns else df['收盘']
        rsi = self._calculate_rsi(close)
        macd_line, signal_line, histogram = self._calculate_macd(close)
        return {
            'rsi': rsi,
            'macd': macd_line,
            'macd_signal': signal_line,
            'macd_histogram': histogram,
        }


class TrendFollowCombo(Strategy):
    """
    趋势跟踪组合策略

    使用 EMA 多头排列 + ADX 趋势强度 + 成交量确认
    """

    def __init__(
        self,
        ema_short: int = 5,
        ema_mid: int = 20,
        ema_long: int = 60,
        adx_period: int = 14,
        adx_threshold: float = 25,
        volume_ratio: float = 1.5,
    ):
        self.ema_short = ema_short
        self.ema_mid = ema_mid
        self.ema_long = ema_long
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.volume_ratio = volume_ratio

    def name(self) -> str:
        return f"TrendFollow({self.ema_short}/{self.ema_mid}/{self.ema_long})"

    def description(self) -> str:
        return f"趋势跟踪 - EMA({self.ema_short}/{self.ema_mid}/{self.ema_long})+ADX({self.adx_period})≥{self.adx_threshold}"

    def _calculate_adx(self, df: pd.DataFrame) -> pd.Series:
        high = df['high'] if 'high' in df.columns else df['最高']
        low = df['low'] if 'low' in df.columns else df['最低']
        close = df['close'] if 'close' in df.columns else df['收盘']

        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        plus_dm[(plus_dm < minus_dm)] = 0
        minus_dm[(minus_dm < plus_dm)] = 0

        tr = pd.concat([
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs()
        ], axis=1).max(axis=1)

        atr = tr.rolling(window=self.adx_period).mean()
        plus_di = 100 * (plus_dm.rolling(window=self.adx_period).mean() / atr.replace(0, np.inf))
        minus_di = 100 * (minus_dm.rolling(window=self.adx_period).mean() / atr.replace(0, np.inf))

        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.inf))
        adx = dx.rolling(window=self.adx_period).mean()
        return adx

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df['close'] if 'close' in df.columns else df['收盘']
        volume = df['volume'] if 'volume' in df.columns else df.get('成交量', pd.Series(0, index=df.index))

        ema_s = close.ewm(span=self.ema_short, adjust=False).mean()
        ema_m = close.ewm(span=self.ema_mid, adjust=False).mean()
        ema_l = close.ewm(span=self.ema_long, adjust=False).mean()

        adx = self._calculate_adx(df)
        vol_avg = volume.rolling(window=20).mean()
        vol_strong = volume > (vol_avg * self.volume_ratio)

        # 多头排列：短 > 中 > 长
        bullish_alignment = (ema_s > ema_m) & (ema_m > ema_l)
        # 空头排列：短 < 中 < 长
        bearish_alignment = (ema_s < ema_m) & (ema_m < ema_l)
        # 趋势够强
        strong_trend = adx > self.adx_threshold

        signals = pd.Series(0, index=df.index, dtype=int)
        signals[bullish_alignment & strong_trend & vol_strong] = 1
        signals[bearish_alignment & strong_trend] = -1

        return signals


class MeanReversionCombo(Strategy):
    """
    均值回归组合策略

    使用布林带 + RSI + 成交量萎缩确认超卖/超买反转
    """

    def __init__(
        self,
        bb_period: int = 20,
        bb_std: float = 2.0,
        rsi_period: int = 14,
        rsi_oversold: float = 30,
        rsi_overbought: float = 70,
        volume_shrink: float = 0.7,
    ):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.volume_shrink = volume_shrink

    def name(self) -> str:
        return f"MeanRevert(BB{self.bb_period}+RSI{self.rsi_period})"

    def description(self) -> str:
        return f"均值回归 - BB({self.bb_period},σ={self.bb_std})+RSI({self.rsi_period})"

    def _calculate_rsi(self, prices: pd.Series) -> pd.Series:
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=self.rsi_period, min_periods=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period, min_periods=self.rsi_period).mean()
        rs = avg_gain / avg_loss.replace(0, np.inf)
        return 100 - (100 / (1 + rs))

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df['close'] if 'close' in df.columns else df['收盘']
        volume = df['volume'] if 'volume' in df.columns else df.get('成交量', pd.Series(0, index=df.index))

        # 布林带
        sma = close.rolling(window=self.bb_period).mean()
        std = close.rolling(window=self.bb_period).std()
        upper = sma + self.bb_std * std
        lower = sma - self.bb_std * std

        rsi = self._calculate_rsi(close)
        vol_avg = volume.rolling(window=20).mean()
        vol_low = volume < (vol_avg * self.volume_shrink)

        # 超卖反转：价格触下轨 + RSI 超卖 + 成交量萎缩（恐慌见底）
        oversold = (close <= lower) & (rsi < self.rsi_oversold)
        # 超买反转：价格触上轨 + RSI 超买
        overbought = (close >= upper) & (rsi > self.rsi_overbought)

        signals = pd.Series(0, index=df.index, dtype=int)
        signals[oversold] = 1
        signals[overbought] = -1

        return signals


def create_default_combo() -> ComboStrategy:
    """创建默认的组合策略（RSI+MACD+趋势跟踪，等权重）"""
    from .advanced_strategies import RSIStrategy, MACDStrategy

    strategies = [
        (RSIStrategy(14, 70, 30), 0.3),
        (MACDStrategy(12, 26, 9), 0.4),
        (TrendFollowCombo(5, 20, 60), 0.3),
    ]
    return ComboStrategy(strategies, buy_threshold=0.5, sell_threshold=-0.5)
