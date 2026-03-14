#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
均线金叉/死叉策略

规则：
- 金叉：短期均线上穿长期均线 → 买入
- 死叉：短期均线下穿长期均线 → 卖出
"""

import pandas as pd
from .base import Strategy


class MACrossStrategy(Strategy):
    """均线交叉策略"""
    
    def __init__(self, short_period: int = 5, long_period: int = 20):
        """
        初始化策略
        
        Args:
            short_period: 短期均线周期
            long_period: 长期均线周期
        """
        self.short_period = short_period
        self.long_period = long_period
    
    def name(self) -> str:
        return f"MA{self.short_period}/{self.long_period}金叉死叉"
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        生成交易信号
        
        信号规则：
        - 1 (买入): 短期均线上穿长期均线（金叉）
        - -1 (卖出): 短期均线下穿长期均线（死叉）
        - 0 (持有): 无交叉
        """
        signals = pd.Series(0, index=df.index)
        
        # 计算均线
        ma_short = df['收盘'].rolling(window=self.short_period).mean()
        ma_long = df['收盘'].rolling(window=self.long_period).mean()
        
        # 金叉：短期从下向上穿过长期
        golden_cross = (ma_short > ma_long) & (ma_short.shift(1) <= ma_long.shift(1))
        
        # 死叉：短期从上向下穿过长期
        death_cross = (ma_short < ma_long) & (ma_short.shift(1) >= ma_long.shift(1))
        
        # 生成信号
        signals[golden_cross] = 1
        signals[death_cross] = -1
        
        return signals


class DualMAStrategy(Strategy):
    """双均线趋势策略"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26):
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def name(self) -> str:
        return f"双均线{self.fast_period}/{self.slow_period}"
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        生成持仓信号（非脉冲式）
        
        规则：
        - 快线 > 慢线 → 持有 (1)
        - 快线 < 慢线 → 空仓 (0)
        """
        ma_fast = df['收盘'].rolling(window=self.fast_period).mean()
        ma_slow = df['收盘'].rolling(window=self.slow_period).mean()
        
        # 持仓信号
        signals = pd.Series(0, index=df.index)
        signals[ma_fast > ma_slow] = 1
        
        return signals
