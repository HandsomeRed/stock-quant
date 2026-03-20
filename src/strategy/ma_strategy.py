#!/usr/bin/env python3
from abc import ABC, abstractmethod
import pandas as pd

class Strategy(ABC):
    """策略基类"""
    @abstractmethod
    def generate_signal(self, df):
        pass

class DualMAStrategy(Strategy):
    """双均线策略"""
    def __init__(self, short_window=12, long_window=26):
        self.short_window = short_window
        self.long_window = long_window
    
    def generate_signal(self, df):
        df = df.copy()
        df['MA_short'] = df['收盘'].rolling(self.short_window).mean()
        df['MA_long'] = df['收盘'].rolling(self.long_window).mean()
        df['signal'] = 0
        df.loc[df['MA_short'] > df['MA_long'], 'signal'] = 1  # 金叉买入
        df.loc[df['MA_short'] < df['MA_long'], 'signal'] = -1  # 死叉卖出
        return df['signal'].iloc[-1]

class Backtester:
    """回测引擎"""
    def __init__(self, initial_capital=100000, commission_rate=0.0003):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
    
    def run(self, df, strategy):
        cash = self.initial_capital
        position = 0
        trades = []
        
        for i in range(1, len(df)):
            signal = strategy.generate_signal(df.iloc[:i+1])
            price = df.iloc[i]['收盘']
            
            if signal == 1 and cash > 0:  # 买入
                volume = int(cash / price / 100) * 100
                if volume > 0:
                    cost = volume * price * (1 + self.commission_rate)
                    if cost <= cash:
                        cash -= cost
                        position = volume
                        trades.append({'type': 'buy', 'price': price, 'volume': volume})
            
            elif signal == -1 and position > 0:  # 卖出
                revenue = position * price * (1 - self.commission_rate)
                cash += revenue
                trades.append({'type': 'sell', 'price': price, 'volume': position})
                position = 0
        
        final_value = cash + position * df.iloc[-1]['收盘']
        return {
            'final_value': final_value,
            'return_rate': (final_value - self.initial_capital) / self.initial_capital * 100,
            'trades': len(trades)
        }
