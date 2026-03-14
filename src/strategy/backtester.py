#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测引擎

功能：
- 运行策略回测
- 计算绩效指标
- 生成交易记录
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from .base import Strategy


class Backtester:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 100000, 
                 commission_rate: float = 0.0003):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
            commission_rate: 手续费率（默认万分之三）
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
    
    def run(self, df: pd.DataFrame, strategy: Strategy) -> Dict:
        """
        运行回测
        
        Args:
            df: 包含 OHLCV 和信号的数据
            strategy: 策略实例
            
        Returns:
            回测结果字典
        """
        # 生成信号
        signals = strategy.generate_signals(df)
        
        # 初始化
        capital = self.initial_capital
        position = 0
        trades = []
        portfolio_values = []
        
        for i in range(len(df)):
            row = df.iloc[i]
            signal = signals.iloc[i]
            price = row['收盘']
            date = row['日期']
            
            # 买入信号
            if signal == 1 and capital > 0:
                # 计算可买入手数（100 股一手）
                shares = int(capital / (price * 100)) * 100
                if shares > 0:
                    cost = shares * price * (1 + self.commission_rate)
                    if cost <= capital:
                        capital -= cost
                        position = shares
                        trades.append({
                            '日期': date,
                            '类型': '买入',
                            '价格': price,
                            '数量': shares,
                            '金额': cost
                        })
            
            # 卖出信号
            elif signal == -1 and position > 0:
                revenue = position * price * (1 - self.commission_rate)
                capital += revenue
                trades.append({
                    '日期': date,
                    '类型': '卖出',
                    '价格': price,
                    '数量': position,
                    '金额': revenue
                })
                position = 0
            
            # 计算组合价值
            portfolio_value = capital + (position * price if position > 0 else 0)
            portfolio_values.append({
                '日期': date,
                '价值': portfolio_value,
                '现金': capital,
                '持仓': position
            })
        
        # 处理未平仓（按最后价格卖出）
        if position > 0:
            final_price = df.iloc[-1]['收盘']
            final_date = df.iloc[-1]['日期']
            revenue = position * final_price * (1 - self.commission_rate)
            capital += revenue
            trades.append({
                '日期': final_date,
                '类型': '卖出 (平仓)',
                '价格': final_price,
                '数量': position,
                '金额': revenue
            })
        
        final_value = capital
        
        return {
            'strategy': strategy.name(),
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': (final_value - self.initial_capital) / self.initial_capital * 100,
            'trades': trades,
            'portfolio_values': pd.DataFrame(portfolio_values),
            'trade_count': len(trades)
        }
    
    def analyze(self, result: Dict, df: pd.DataFrame) -> Dict:
        """
        分析回测结果
        
        Args:
            result: 回测结果
            df: 原始数据
            
        Returns:
            绩效指标字典
        """
        portfolio = result['portfolio_values']
        
        # 计算每日收益率
        portfolio['收益率'] = portfolio['价值'].pct_change()
        
        # 总收益率
        total_return = result['total_return']
        
        # 年化收益率
        days = len(df)
        annual_return = (1 + total_return/100) ** (252/days) - 1
        
        # 波动率
        volatility = portfolio['收益率'].std() * np.sqrt(252) * 100
        
        # 夏普比率（假设无风险利率 3%）
        risk_free_rate = 0.03
        sharpe_ratio = (annual_return - risk_free_rate) / (volatility/100) if volatility > 0 else 0
        
        # 最大回撤
        portfolio['最高值'] = portfolio['价值'].cummax()
        portfolio['回撤'] = (portfolio['最高值'] - portfolio['价值']) / portfolio['最高值'] * 100
        max_drawdown = portfolio['回撤'].max()
        
        # 胜率
        trades_df = pd.DataFrame(result['trades'])
        if len(trades_df) > 0:
            # 配对买卖
            buys = trades_df[trades_df['类型'] == '买入']
            sells = trades_df[trades_df['类型'].str.contains('卖出')]
            
            profitable_trades = 0
            total_trades = min(len(buys), len(sells))
            
            for i in range(total_trades):
                buy_price = buys.iloc[i]['价格']
                sell_price = sells.iloc[i]['价格']
                if sell_price > buy_price:
                    profitable_trades += 1
            
            win_rate = profitable_trades / total_trades * 100 if total_trades > 0 else 0
        else:
            win_rate = 0
        
        return {
            '总收益率': f"{total_return:.2f}%",
            '年化收益率': f"{annual_return*100:.2f}%",
            '波动率': f"{volatility:.2f}%",
            '夏普比率': f"{sharpe_ratio:.2f}",
            '最大回撤': f"{max_drawdown:.2f}%",
            '交易次数': result['trade_count'],
            '胜率': f"{win_rate:.2f}%",
            '最终价值': f"{result['final_value']:.2f}元"
        }
