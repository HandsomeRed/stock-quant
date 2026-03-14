#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略模块单元测试
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 添加路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from strategy.base import Strategy
from strategy.ma_cross import MACrossStrategy, DualMAStrategy
from strategy.backtester import Backtester


@pytest.fixture
def sample_data():
    """创建示例股票数据"""
    dates = pd.date_range('2024-01-01', periods=100)
    prices = np.random.uniform(10, 20, 100)
    
    return pd.DataFrame({
        '日期': dates,
        '收盘': prices,
        '开盘': prices * 0.99,
        '最高': prices * 1.02,
        '最低': prices * 0.98,
        '成交量': np.random.randint(1000, 10000, 100)
    })


class TestMACrossStrategy:
    """测试均线交叉策略"""
    
    def test_signal_generation(self, sample_data):
        """测试信号生成"""
        strategy = MACrossStrategy(short_period=5, long_period=20)
        signals = strategy.generate_signals(sample_data)
        
        assert len(signals) == len(sample_data)
        assert set(signals.unique()).issubset({-1, 0, 1})
    
    def test_strategy_name(self):
        """测试策略名称"""
        strategy = MACrossStrategy(short_period=5, long_period=20)
        name = strategy.name()
        assert "MA" in name and "5" in name and "20" in name and "金叉" in name
    
    def test_golden_cross_detection(self):
        """测试金叉检测"""
        # 创建明显金叉的数据
        prices = [10] * 20 + [10, 11, 12, 13, 14, 15]  # 上涨趋势
        df = pd.DataFrame({'收盘': prices})
        
        strategy = MACrossStrategy(short_period=3, long_period=10)
        signals = strategy.generate_signals(df)
        
        # 应该有买入信号
        assert (signals == 1).any()


class TestDualMAStrategy:
    """测试双均线策略"""
    
    def test_position_signals(self, sample_data):
        """测试持仓信号"""
        strategy = DualMAStrategy(fast_period=12, slow_period=26)
        signals = strategy.generate_signals(sample_data)
        
        assert len(signals) == len(sample_data)
        assert set(signals.unique()).issubset({0, 1})
    
    def test_strategy_name(self):
        """测试策略名称"""
        strategy = DualMAStrategy(fast_period=12, slow_period=26)
        assert "双均线" in strategy.name() and "12" in strategy.name() and "26" in strategy.name()


class TestBacktester:
    """测试回测引擎"""
    
    def test_initialization(self):
        """测试初始化"""
        backtester = Backtester(initial_capital=50000, commission_rate=0.0005)
        assert backtester.initial_capital == 50000
        assert backtester.commission_rate == 0.0005
    
    def test_run_backtest(self, sample_data):
        """测试运行回测"""
        strategy = MACrossStrategy(short_period=5, long_period=20)
        backtester = Backtester(initial_capital=100000)
        
        result = backtester.run(sample_data, strategy)
        
        assert 'initial_capital' in result
        assert 'final_value' in result
        assert 'total_return' in result
        assert 'trades' in result
        assert 'portfolio_values' in result
    
    def test_analyze_results(self, sample_data):
        """测试结果分析"""
        strategy = MACrossStrategy(short_period=5, long_period=20)
        backtester = Backtester(initial_capital=100000)
        
        result = backtester.run(sample_data, strategy)
        metrics = backtester.analyze(result, sample_data)
        
        assert '总收益率' in metrics
        assert '年化收益率' in metrics
        assert '夏普比率' in metrics
        assert '最大回撤' in metrics
        assert '交易次数' in metrics
        assert '胜率' in metrics
    
    def test_commission_calculation(self, sample_data):
        """测试手续费计算"""
        strategy = DualMAStrategy(fast_period=5, slow_period=10)
        
        # 高手续费率
        backtester_high = Backtester(initial_capital=100000, commission_rate=0.001)
        result_high = backtester_high.run(sample_data, strategy)
        
        # 低手续费率
        backtester_low = Backtester(initial_capital=100000, commission_rate=0.0001)
        result_low = backtester_low.run(sample_data, strategy)
        
        # 高手续费应该收益更低（或亏损更多）
        assert result_high['final_value'] <= result_low['final_value']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
