#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级策略 + 策略对比引擎 测试

Stage 3b: 策略库扩展 + 对比分析
"""

import pytest
import pandas as pd
import numpy as np
from src.strategy.advanced_strategies import (
    RSIStrategy, BollingerBandStrategy, MACDStrategy, VolumeBreakoutStrategy
)
from src.strategy.comparator import StrategyComparator, RiskAnalyzer
from src.strategy.ma_cross import MACrossStrategy
from src.strategy.backtester import Backtester


# ==================== 测试数据生成 ====================

def generate_test_data(days: int = 200, start_price: float = 10.0, 
                       trend: str = 'up', volatility: float = 0.02) -> pd.DataFrame:
    """生成测试用股票数据"""
    np.random.seed(42)
    dates = pd.date_range('2025-01-01', periods=days, freq='B')
    
    prices = [start_price]
    volumes = []
    
    for i in range(1, days):
        if trend == 'up':
            drift = 0.001
        elif trend == 'down':
            drift = -0.001
        else:
            drift = 0
        
        change = drift + volatility * np.random.randn()
        new_price = prices[-1] * (1 + change)
        prices.append(max(0.1, new_price))
        
    for i in range(days):
        base_vol = 1000000
        vol = int(base_vol * (1 + 0.5 * abs(np.random.randn())))
        volumes.append(vol)
    
    df = pd.DataFrame({
        '日期': dates,
        '开盘': [p * (1 - 0.005 * abs(np.random.randn())) for p in prices],
        '最高': [p * (1 + 0.01 * abs(np.random.randn())) for p in prices],
        '最低': [p * (1 - 0.01 * abs(np.random.randn())) for p in prices],
        '收盘': prices,
        '成交量': volumes,
    })
    
    return df


# ==================== RSI 策略测试 ====================

class TestRSIStrategy:
    def test_init(self):
        s = RSIStrategy()
        assert s.period == 14
        assert s.overbought == 70
        assert s.oversold == 30
    
    def test_custom_params(self):
        s = RSIStrategy(period=7, overbought=80, oversold=20)
        assert s.period == 7
        assert s.overbought == 80
    
    def test_name(self):
        s = RSIStrategy()
        assert 'RSI' in s.name()
    
    def test_calculate_rsi(self):
        df = generate_test_data(100)
        s = RSIStrategy()
        rsi = s.calculate_rsi(df['收盘'])
        assert len(rsi) == 100
        # RSI should be between 0 and 100 (where not NaN)
        valid = rsi.dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()
    
    def test_generate_signals(self):
        df = generate_test_data(200)
        s = RSIStrategy()
        signals = s.generate_signals(df)
        assert len(signals) == 200
        assert set(signals.unique()).issubset({-1, 0, 1})
    
    def test_backtest(self):
        df = generate_test_data(200)
        s = RSIStrategy()
        bt = Backtester()
        result = bt.run(df, s)
        assert result['final_value'] > 0
        assert result['strategy'] == s.name()


# ==================== 布林带策略测试 ====================

class TestBollingerBandStrategy:
    def test_init(self):
        s = BollingerBandStrategy()
        assert s.period == 20
        assert s.num_std == 2.0
    
    def test_name(self):
        s = BollingerBandStrategy()
        assert 'Bollinger' in s.name()
    
    def test_generate_signals(self):
        df = generate_test_data(200)
        s = BollingerBandStrategy()
        signals = s.generate_signals(df)
        assert len(signals) == 200
        assert set(signals.unique()).issubset({-1, 0, 1})
    
    def test_backtest(self):
        df = generate_test_data(200)
        s = BollingerBandStrategy()
        bt = Backtester()
        result = bt.run(df, s)
        assert result['final_value'] > 0


# ==================== MACD 策略测试 ====================

class TestMACDStrategy:
    def test_init(self):
        s = MACDStrategy()
        assert s.fast == 12
        assert s.slow == 26
        assert s.signal_period == 9
    
    def test_name(self):
        s = MACDStrategy()
        assert 'MACD' in s.name()
    
    def test_generate_signals(self):
        df = generate_test_data(200)
        s = MACDStrategy()
        signals = s.generate_signals(df)
        assert len(signals) == 200
        assert set(signals.unique()).issubset({-1, 0, 1})
    
    def test_backtest(self):
        df = generate_test_data(200)
        s = MACDStrategy()
        bt = Backtester()
        result = bt.run(df, s)
        assert result['final_value'] > 0
    
    def test_signals_contain_buys_and_sells(self):
        df = generate_test_data(300)
        s = MACDStrategy()
        signals = s.generate_signals(df)
        # MACD should generate some signals in 300 days
        assert (signals != 0).sum() > 0


# ==================== 放量突破策略测试 ====================

class TestVolumeBreakoutStrategy:
    def test_init(self):
        s = VolumeBreakoutStrategy()
        assert s.price_period == 20
        assert s.volume_ratio == 2.0
    
    def test_name(self):
        s = VolumeBreakoutStrategy()
        assert '放量突破' in s.name()
    
    def test_generate_signals(self):
        df = generate_test_data(200)
        s = VolumeBreakoutStrategy()
        signals = s.generate_signals(df)
        assert len(signals) == 200
        assert set(signals.unique()).issubset({-1, 0, 1})
    
    def test_backtest(self):
        df = generate_test_data(200)
        s = VolumeBreakoutStrategy()
        bt = Backtester()
        result = bt.run(df, s)
        assert result['final_value'] > 0


# ==================== 策略对比引擎测试 ====================

class TestStrategyComparator:
    def setup_method(self):
        self.df = generate_test_data(200)
        self.strategies = [
            MACrossStrategy(5, 20),
            RSIStrategy(),
            BollingerBandStrategy(),
            MACDStrategy(),
        ]
    
    def test_compare(self):
        comp = StrategyComparator()
        result = comp.compare(self.df, self.strategies)
        assert result['strategies_count'] == 4
        assert len(result['results']) == 4
        assert result['best_strategy'] is not None
    
    def test_results_sorted_by_return(self):
        comp = StrategyComparator()
        result = comp.compare(self.df, self.strategies)
        returns = [r['total_return'] for r in result['results']]
        assert returns == sorted(returns, reverse=True)
    
    def test_buy_hold_return(self):
        comp = StrategyComparator()
        result = comp.compare(self.df, self.strategies)
        assert isinstance(result['buy_hold_return'], float)
    
    def test_generate_report(self):
        comp = StrategyComparator()
        result = comp.compare(self.df, self.strategies)
        report = comp.generate_report(result)
        assert '策略对比报告' in report
        assert '最优策略' in report
    
    def test_get_summary_df(self):
        comp = StrategyComparator()
        result = comp.compare(self.df, self.strategies)
        summary = comp.get_summary_df(result)
        assert isinstance(summary, pd.DataFrame)
        assert len(summary) == 4
        assert '策略' in summary.columns
    
    def test_single_strategy(self):
        comp = StrategyComparator()
        result = comp.compare(self.df, [RSIStrategy()])
        assert result['strategies_count'] == 1
        assert result['best_strategy'] == result['worst_strategy']
    
    def test_custom_capital(self):
        comp = StrategyComparator(initial_capital=50000)
        result = comp.compare(self.df, [RSIStrategy()])
        # All results should use the custom capital
        assert result['results'][0]['backtest']['initial_capital'] == 50000


# ==================== 风险分析器测试 ====================

class TestRiskAnalyzer:
    def setup_method(self):
        np.random.seed(42)
        self.returns = pd.Series(np.random.randn(252) * 0.02)
        self.portfolio = pd.Series(np.cumsum(np.random.randn(252) * 100) + 100000)
        self.portfolio = self.portfolio.clip(lower=50000)
    
    def test_var(self):
        var = RiskAnalyzer.calculate_var(self.returns)
        assert isinstance(var, float)
        assert var < 0  # VaR should be negative (potential loss)
    
    def test_cvar(self):
        cvar = RiskAnalyzer.calculate_cvar(self.returns)
        assert isinstance(cvar, float)
        var = RiskAnalyzer.calculate_var(self.returns)
        assert cvar <= var  # CVaR should be worse than VaR
    
    def test_sortino(self):
        sortino = RiskAnalyzer.calculate_sortino(self.returns)
        assert isinstance(sortino, float)
    
    def test_calmar(self):
        calmar = RiskAnalyzer.calculate_calmar(20.0, 10.0, 1.0)
        assert calmar == 2.0
    
    def test_calmar_zero_drawdown(self):
        calmar = RiskAnalyzer.calculate_calmar(20.0, 0, 1.0)
        assert calmar == 0
    
    def test_analyze_drawdowns(self):
        result = RiskAnalyzer.analyze_drawdowns(self.portfolio)
        assert 'max_drawdown' in result
        assert 'avg_drawdown_days' in result
        assert result['max_drawdown'] >= 0
    
    def test_risk_report(self):
        report = RiskAnalyzer.risk_report(self.portfolio, 10.0, 252)
        assert 'VaR_95' in report
        assert 'CVaR_95' in report
        assert 'Sortino比率' in report
        assert 'Calmar比率' in report
        assert '最大回撤' in report
    
    def test_empty_returns(self):
        empty = pd.Series([], dtype=float)
        assert RiskAnalyzer.calculate_var(empty) == 0
        assert RiskAnalyzer.calculate_cvar(empty) == 0
        assert RiskAnalyzer.calculate_sortino(empty) == 0
    
    def test_var_confidence_levels(self):
        var_95 = RiskAnalyzer.calculate_var(self.returns, 0.95)
        var_99 = RiskAnalyzer.calculate_var(self.returns, 0.99)
        # 99% VaR should be more extreme than 95%
        assert var_99 <= var_95
