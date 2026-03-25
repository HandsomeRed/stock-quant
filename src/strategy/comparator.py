#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略对比引擎 - 多策略横向比较

功能：
- 同一股票多策略回测对比
- 绩效指标横向比较
- 最优策略推荐
- 策略组合回测
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from .base import Strategy
from .backtester import Backtester


class StrategyComparator:
    """策略对比引擎"""
    
    def __init__(self, initial_capital: float = 100000, commission_rate: float = 0.0003):
        self.backtester = Backtester(initial_capital, commission_rate)
        self.initial_capital = initial_capital
    
    def compare(self, df: pd.DataFrame, strategies: List[Strategy]) -> Dict:
        """
        对比多个策略的回测结果
        
        Args:
            df: 股票数据
            strategies: 策略列表
            
        Returns:
            对比结果字典
        """
        results = []
        
        for strategy in strategies:
            try:
                result = self.backtester.run(df, strategy)
                analysis = self.backtester.analyze(result, df)
                results.append({
                    'strategy_name': strategy.name(),
                    'description': strategy.description(),
                    'backtest': result,
                    'analysis': analysis,
                    'total_return': result['total_return'],
                    'final_value': result['final_value'],
                    'trade_count': result['trade_count'],
                })
            except Exception as e:
                results.append({
                    'strategy_name': strategy.name(),
                    'description': strategy.description(),
                    'error': str(e),
                    'total_return': 0,
                    'final_value': self.initial_capital,
                    'trade_count': 0,
                })
        
        # 排序：按总收益率降序
        results.sort(key=lambda x: x['total_return'], reverse=True)
        
        # 基准：买入持有
        buy_hold_return = 0
        if len(df) >= 2:
            close_col = '收盘' if '收盘' in df.columns else 'close'
            first_price = df[close_col].iloc[0]
            last_price = df[close_col].iloc[-1]
            if first_price > 0:
                buy_hold_return = (last_price - first_price) / first_price * 100
        
        return {
            'results': results,
            'best_strategy': results[0]['strategy_name'] if results else None,
            'worst_strategy': results[-1]['strategy_name'] if results else None,
            'buy_hold_return': buy_hold_return,
            'strategies_count': len(strategies),
            'data_days': len(df),
        }
    
    def generate_report(self, comparison: Dict) -> str:
        """
        生成对比报告（文本格式）
        """
        lines = []
        lines.append("=" * 60)
        lines.append("📊 策略对比报告")
        lines.append("=" * 60)
        lines.append(f"对比策略数：{comparison['strategies_count']}")
        lines.append(f"数据天数：{comparison['data_days']}")
        lines.append(f"买入持有收益：{comparison['buy_hold_return']:.2f}%")
        lines.append("")
        lines.append("-" * 60)
        lines.append(f"{'策略名称':<25} {'收益率':>10} {'交易次数':>8} {'状态':>6}")
        lines.append("-" * 60)
        
        for r in comparison['results']:
            status = "✅" if r['total_return'] > comparison['buy_hold_return'] else "❌"
            if 'error' in r:
                status = "⚠️"
            lines.append(f"{r['strategy_name']:<25} {r['total_return']:>9.2f}% {r['trade_count']:>8} {status:>6}")
        
        lines.append("-" * 60)
        lines.append(f"🏆 最优策略：{comparison['best_strategy']}")
        lines.append(f"📉 最差策略：{comparison['worst_strategy']}")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def get_summary_df(self, comparison: Dict) -> pd.DataFrame:
        """
        获取对比摘要DataFrame
        """
        rows = []
        for r in comparison['results']:
            row = {
                '策略': r['strategy_name'],
                '总收益率': f"{r['total_return']:.2f}%",
                '最终价值': f"{r['final_value']:.0f}",
                '交易次数': r['trade_count'],
            }
            if 'analysis' in r:
                row.update(r['analysis'])
            if 'error' in r:
                row['备注'] = r['error']
            rows.append(row)
        
        return pd.DataFrame(rows)


class RiskAnalyzer:
    """风险分析器"""
    
    @staticmethod
    def calculate_var(returns: pd.Series, confidence: float = 0.95) -> float:
        """
        计算 VaR (Value at Risk)
        
        Args:
            returns: 收益率序列
            confidence: 置信度
            
        Returns:
            VaR 值（负数表示潜在损失）
        """
        if len(returns) == 0:
            return 0
        clean = returns.dropna()
        if len(clean) == 0:
            return 0
        return float(np.percentile(clean, (1 - confidence) * 100))
    
    @staticmethod
    def calculate_cvar(returns: pd.Series, confidence: float = 0.95) -> float:
        """
        计算 CVaR (Conditional VaR / Expected Shortfall)
        """
        if len(returns) == 0:
            return 0
        clean = returns.dropna()
        if len(clean) == 0:
            return 0
        var = np.percentile(clean, (1 - confidence) * 100)
        return float(clean[clean <= var].mean()) if len(clean[clean <= var]) > 0 else var
    
    @staticmethod
    def calculate_sortino(returns: pd.Series, risk_free: float = 0.03, periods: int = 252) -> float:
        """
        计算 Sortino 比率（只考虑下行风险）
        """
        if len(returns) == 0:
            return 0
        clean = returns.dropna()
        if len(clean) == 0:
            return 0
        excess_return = clean.mean() * periods - risk_free
        downside = clean[clean < 0]
        downside_std = downside.std() * np.sqrt(periods) if len(downside) > 0 else 0
        return float(excess_return / downside_std) if downside_std > 0 else 0
    
    @staticmethod
    def calculate_calmar(total_return: float, max_drawdown: float, years: float) -> float:
        """
        计算 Calmar 比率（收益/最大回撤）
        """
        if max_drawdown == 0 or years == 0:
            return 0
        annual_return = total_return / years
        return annual_return / max_drawdown
    
    @staticmethod
    def analyze_drawdowns(portfolio_values: pd.Series) -> Dict:
        """
        分析回撤详情
        """
        peak = portfolio_values.cummax()
        drawdown = (peak - portfolio_values) / peak * 100
        
        max_dd = drawdown.max()
        max_dd_idx = drawdown.idxmax() if max_dd > 0 else None
        
        # 回撤持续天数
        in_drawdown = drawdown > 0
        dd_periods = []
        current_dd_start = None
        
        for i in range(len(in_drawdown)):
            if in_drawdown.iloc[i] and current_dd_start is None:
                current_dd_start = i
            elif not in_drawdown.iloc[i] and current_dd_start is not None:
                dd_periods.append(i - current_dd_start)
                current_dd_start = None
        
        if current_dd_start is not None:
            dd_periods.append(len(in_drawdown) - current_dd_start)
        
        return {
            'max_drawdown': max_dd,
            'max_drawdown_index': max_dd_idx,
            'avg_drawdown_days': np.mean(dd_periods) if dd_periods else 0,
            'max_drawdown_days': max(dd_periods) if dd_periods else 0,
            'drawdown_count': len(dd_periods),
        }
    
    @staticmethod
    def risk_report(portfolio_values: pd.Series, total_return: float, days: int) -> Dict:
        """
        生成完整风险报告
        """
        returns = portfolio_values.pct_change().dropna()
        years = days / 252
        
        dd_analysis = RiskAnalyzer.analyze_drawdowns(portfolio_values)
        
        return {
            'VaR_95': f"{RiskAnalyzer.calculate_var(returns, 0.95) * 100:.2f}%",
            'CVaR_95': f"{RiskAnalyzer.calculate_cvar(returns, 0.95) * 100:.2f}%",
            'Sortino比率': f"{RiskAnalyzer.calculate_sortino(returns):.2f}",
            'Calmar比率': f"{RiskAnalyzer.calculate_calmar(total_return, dd_analysis['max_drawdown'], years):.2f}",
            '最大回撤': f"{dd_analysis['max_drawdown']:.2f}%",
            '平均回撤天数': f"{dd_analysis['avg_drawdown_days']:.0f}天",
            '最长回撤天数': f"{dd_analysis['max_drawdown_days']}天",
            '回撤次数': dd_analysis['drawdown_count'],
        }
