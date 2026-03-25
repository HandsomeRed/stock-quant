#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSI 策略 - 相对强弱指标策略

买入条件：RSI 从超卖区回升（RSI < oversold 后回升到 oversold 上方）
卖出条件：RSI 进入超买区（RSI > overbought）
"""

import pandas as pd
import numpy as np
from .base import Strategy


class RSIStrategy(Strategy):
    """RSI 策略"""
    
    def __init__(self, period: int = 14, overbought: float = 70, oversold: float = 30):
        """
        初始化 RSI 策略
        
        Args:
            period: RSI 计算周期
            overbought: 超买阈值
            oversold: 超卖阈值
        """
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    def name(self) -> str:
        return f"RSI({self.period}, {self.overbought}/{self.oversold})"
    
    def description(self) -> str:
        return f"RSI策略 - 周期{self.period}, 超买{self.overbought}/超卖{self.oversold}"
    
    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=self.period, min_periods=self.period).mean()
        avg_loss = loss.rolling(window=self.period, min_periods=self.period).mean()
        
        rs = avg_gain / avg_loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        生成RSI交易信号
        
        买入：RSI从超卖区回升（前一日<oversold, 当日>=oversold）
        卖出：RSI进入超买区（RSI >= overbought）
        """
        close_col = '收盘' if '收盘' in df.columns else 'close'
        rsi = self.calculate_rsi(df[close_col])
        
        signals = pd.Series(0, index=df.index)
        
        for i in range(1, len(rsi)):
            if pd.isna(rsi.iloc[i]) or pd.isna(rsi.iloc[i-1]):
                continue
            # 买入：从超卖区回升
            if rsi.iloc[i-1] < self.oversold and rsi.iloc[i] >= self.oversold:
                signals.iloc[i] = 1
            # 卖出：进入超买区
            elif rsi.iloc[i] >= self.overbought:
                signals.iloc[i] = -1
        
        return signals


class BollingerBandStrategy(Strategy):
    """布林带策略"""
    
    def __init__(self, period: int = 20, num_std: float = 2.0):
        """
        初始化布林带策略
        
        Args:
            period: 移动平均周期
            num_std: 标准差倍数
        """
        self.period = period
        self.num_std = num_std
    
    def name(self) -> str:
        return f"Bollinger({self.period}, {self.num_std}σ)"
    
    def description(self) -> str:
        return f"布林带策略 - {self.period}日均线, {self.num_std}倍标准差"
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        生成布林带交易信号
        
        买入：价格触及下轨后回升
        卖出：价格触及上轨
        """
        close_col = '收盘' if '收盘' in df.columns else 'close'
        prices = df[close_col]
        
        middle = prices.rolling(window=self.period).mean()
        std = prices.rolling(window=self.period).std()
        upper = middle + self.num_std * std
        lower = middle - self.num_std * std
        
        signals = pd.Series(0, index=df.index)
        
        for i in range(1, len(prices)):
            if pd.isna(lower.iloc[i]) or pd.isna(upper.iloc[i]):
                continue
            # 买入：价格从下轨回升
            if prices.iloc[i-1] <= lower.iloc[i-1] and prices.iloc[i] > lower.iloc[i]:
                signals.iloc[i] = 1
            # 卖出：价格触及上轨
            elif prices.iloc[i] >= upper.iloc[i]:
                signals.iloc[i] = -1
        
        return signals


class MACDStrategy(Strategy):
    """MACD 策略"""
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        """
        初始化 MACD 策略
        
        Args:
            fast: 快线EMA周期
            slow: 慢线EMA周期
            signal: 信号线周期
        """
        self.fast = fast
        self.slow = slow
        self.signal_period = signal
    
    def name(self) -> str:
        return f"MACD({self.fast},{self.slow},{self.signal_period})"
    
    def description(self) -> str:
        return f"MACD策略 - 快{self.fast}/慢{self.slow}/信号{self.signal_period}"
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        生成MACD交易信号
        
        买入：MACD金叉（DIF上穿DEA）
        卖出：MACD死叉（DIF下穿DEA）
        """
        close_col = '收盘' if '收盘' in df.columns else 'close'
        prices = df[close_col]
        
        ema_fast = prices.ewm(span=self.fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=self.signal_period, adjust=False).mean()
        
        signals = pd.Series(0, index=df.index)
        
        for i in range(1, len(dif)):
            if pd.isna(dif.iloc[i]) or pd.isna(dea.iloc[i]):
                continue
            # 金叉买入
            if dif.iloc[i-1] <= dea.iloc[i-1] and dif.iloc[i] > dea.iloc[i]:
                signals.iloc[i] = 1
            # 死叉卖出
            elif dif.iloc[i-1] >= dea.iloc[i-1] and dif.iloc[i] < dea.iloc[i]:
                signals.iloc[i] = -1
        
        return signals


class VolumeBreakoutStrategy(Strategy):
    """放量突破策略"""
    
    def __init__(self, price_period: int = 20, volume_ratio: float = 2.0):
        """
        初始化放量突破策略
        
        Args:
            price_period: 价格突破观察周期
            volume_ratio: 成交量放大倍数阈值
        """
        self.price_period = price_period
        self.volume_ratio = volume_ratio
    
    def name(self) -> str:
        return f"放量突破({self.price_period}日, {self.volume_ratio}x)"
    
    def description(self) -> str:
        return f"放量突破策略 - {self.price_period}日新高+{self.volume_ratio}倍量"
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        生成放量突破交易信号
        
        买入：价格创N日新高 + 成交量放大
        卖出：价格跌破N日均线
        """
        close_col = '收盘' if '收盘' in df.columns else 'close'
        vol_col = '成交量' if '成交量' in df.columns else 'volume'
        
        prices = df[close_col]
        volumes = df[vol_col]
        
        highest = prices.rolling(window=self.price_period).max()
        avg_volume = volumes.rolling(window=self.price_period).mean()
        ma = prices.rolling(window=self.price_period).mean()
        
        signals = pd.Series(0, index=df.index)
        
        for i in range(self.price_period, len(prices)):
            if pd.isna(highest.iloc[i]) or pd.isna(avg_volume.iloc[i]):
                continue
            # 买入：创新高 + 放量
            if (prices.iloc[i] >= highest.iloc[i] and 
                avg_volume.iloc[i] > 0 and
                volumes.iloc[i] >= avg_volume.iloc[i] * self.volume_ratio):
                signals.iloc[i] = 1
            # 卖出：跌破均线
            elif prices.iloc[i] < ma.iloc[i]:
                signals.iloc[i] = -1
        
        return signals
