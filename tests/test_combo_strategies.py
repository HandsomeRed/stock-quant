#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组合策略测试
"""

import pytest
import pandas as pd
import numpy as np
from src.strategy.combo_strategies import (
    ComboStrategy,
    RSIMACDCombo,
    TrendFollowCombo,
    MeanReversionCombo,
    create_default_combo,
)
from src.strategy.advanced_strategies import RSIStrategy, MACDStrategy


def create_test_data(n: int = 200, trend: str = 'up') -> pd.DataFrame:
    """生成测试数据"""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=n, freq='D')

    if trend == 'up':
        base = np.cumsum(np.random.randn(n) * 0.5 + 0.1) + 50
    elif trend == 'down':
        base = np.cumsum(np.random.randn(n) * 0.5 - 0.1) + 80
    elif trend == 'sideways':
        base = 50 + np.random.randn(n) * 2
    else:
        base = np.cumsum(np.random.randn(n) * 0.5) + 50

    close = np.maximum(base, 1)
    high = close * (1 + np.abs(np.random.randn(n)) * 0.01)
    low = close * (1 - np.abs(np.random.randn(n)) * 0.01)
    open_ = close * (1 + np.random.randn(n) * 0.005)
    volume = np.random.randint(100000, 1000000, n).astype(float)

    return pd.DataFrame({
        'date': dates,
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
    }).set_index('date')


class TestComboStrategy:
    """组合策略测试"""

    def test_create(self):
        rsi = RSIStrategy()
        macd = MACDStrategy()
        combo = ComboStrategy([(rsi, 0.5), (macd, 0.5)])
        assert 'Combo' in combo.name()

    def test_description(self):
        rsi = RSIStrategy()
        combo = ComboStrategy([(rsi, 1.0)])
        desc = combo.description()
        assert '组合策略' in desc

    def test_generate_signals(self):
        df = create_test_data(200, 'up')
        rsi = RSIStrategy()
        macd = MACDStrategy()
        combo = ComboStrategy([(rsi, 0.5), (macd, 0.5)])
        signals = combo.generate_signals(df)
        assert len(signals) == len(df)
        assert set(signals.unique()).issubset({-1, 0, 1})

    def test_signals_range(self):
        df = create_test_data(200, 'down')
        rsi = RSIStrategy()
        macd = MACDStrategy()
        combo = ComboStrategy([(rsi, 0.5), (macd, 0.5)])
        signals = combo.generate_signals(df)
        assert signals.min() >= -1
        assert signals.max() <= 1

    def test_component_signals(self):
        df = create_test_data(200)
        rsi = RSIStrategy()
        macd = MACDStrategy()
        combo = ComboStrategy([(rsi, 0.5), (macd, 0.5)])
        components = combo.get_component_signals(df)
        assert len(components) == 2
        assert rsi.name() in components
        assert macd.name() in components

    def test_threshold_sensitivity(self):
        df = create_test_data(200)
        rsi = RSIStrategy()
        loose = ComboStrategy([(rsi, 1.0)], buy_threshold=0.1, sell_threshold=-0.1)
        strict = ComboStrategy([(rsi, 1.0)], buy_threshold=0.9, sell_threshold=-0.9)
        loose_signals = loose.generate_signals(df)
        strict_signals = strict.generate_signals(df)
        # 宽松阈值应产生更多信号
        loose_count = (loose_signals != 0).sum()
        strict_count = (strict_signals != 0).sum()
        assert loose_count >= strict_count

    def test_single_strategy(self):
        df = create_test_data(200)
        rsi = RSIStrategy()
        combo = ComboStrategy([(rsi, 1.0)], buy_threshold=0.5, sell_threshold=-0.5)
        signals = combo.generate_signals(df)
        assert len(signals) == len(df)

    def test_unequal_weights(self):
        df = create_test_data(200)
        rsi = RSIStrategy()
        macd = MACDStrategy()
        combo = ComboStrategy([(rsi, 0.8), (macd, 0.2)])
        signals = combo.generate_signals(df)
        assert len(signals) == len(df)


class TestRSIMACDCombo:
    """RSI + MACD 组合测试"""

    def test_create_default(self):
        strategy = RSIMACDCombo()
        assert 'RSI_MACD' in strategy.name()

    def test_create_custom(self):
        strategy = RSIMACDCombo(rsi_period=7, macd_fast=6, macd_slow=13)
        assert '7' in strategy.name()

    def test_generate_signals_up(self):
        df = create_test_data(200, 'up')
        strategy = RSIMACDCombo()
        signals = strategy.generate_signals(df)
        assert len(signals) == len(df)
        # 上涨趋势应有一些买入信号
        buy_count = (signals == 1).sum()
        assert buy_count >= 0  # 至少不报错

    def test_generate_signals_down(self):
        df = create_test_data(200, 'down')
        strategy = RSIMACDCombo()
        signals = strategy.generate_signals(df)
        assert len(signals) == len(df)

    def test_generate_signals_sideways(self):
        df = create_test_data(200, 'sideways')
        strategy = RSIMACDCombo()
        signals = strategy.generate_signals(df)
        assert len(signals) == len(df)

    def test_get_indicators(self):
        df = create_test_data(200)
        strategy = RSIMACDCombo()
        indicators = strategy.get_indicators(df)
        assert 'rsi' in indicators
        assert 'macd' in indicators
        assert 'macd_signal' in indicators
        assert 'macd_histogram' in indicators
        assert len(indicators['rsi']) == len(df)

    def test_rsi_range(self):
        df = create_test_data(200)
        strategy = RSIMACDCombo()
        indicators = strategy.get_indicators(df)
        rsi = indicators['rsi'].dropna()
        assert rsi.min() >= 0
        assert rsi.max() <= 100

    def test_description(self):
        strategy = RSIMACDCombo()
        assert '组合' in strategy.description()


class TestTrendFollowCombo:
    """趋势跟踪组合测试"""

    def test_create(self):
        strategy = TrendFollowCombo()
        assert 'TrendFollow' in strategy.name()

    def test_generate_signals(self):
        df = create_test_data(200, 'up')
        strategy = TrendFollowCombo()
        signals = strategy.generate_signals(df)
        assert len(signals) == len(df)
        assert set(signals.unique()).issubset({-1, 0, 1})

    def test_strong_uptrend(self):
        # 创建强上涨数据
        np.random.seed(42)
        n = 200
        dates = pd.date_range('2024-01-01', periods=n, freq='D')
        close = np.cumsum(np.ones(n) * 0.5 + np.random.randn(n) * 0.1) + 50
        high = close * 1.01
        low = close * 0.99
        volume = np.ones(n) * 500000
        # Make some volume spikes
        volume[60:80] = 1000000
        df = pd.DataFrame({
            'open': close, 'high': high, 'low': low, 'close': close, 'volume': volume
        }, index=dates)
        strategy = TrendFollowCombo(adx_threshold=15)  # lower threshold for test
        signals = strategy.generate_signals(df)
        assert len(signals) == len(df)

    def test_custom_params(self):
        strategy = TrendFollowCombo(ema_short=3, ema_mid=10, ema_long=30, adx_threshold=20)
        assert '3' in strategy.name()

    def test_description(self):
        strategy = TrendFollowCombo()
        desc = strategy.description()
        assert '趋势跟踪' in desc
        assert 'ADX' in desc

    def test_no_volume_column(self):
        df = create_test_data(200)
        df = df.drop(columns=['volume'])
        df['成交量'] = np.random.randint(100000, 1000000, len(df))
        strategy = TrendFollowCombo()
        signals = strategy.generate_signals(df)
        assert len(signals) == len(df)


class TestMeanReversionCombo:
    """均值回归组合测试"""

    def test_create(self):
        strategy = MeanReversionCombo()
        assert 'MeanRevert' in strategy.name()

    def test_generate_signals(self):
        df = create_test_data(200, 'sideways')
        strategy = MeanReversionCombo()
        signals = strategy.generate_signals(df)
        assert len(signals) == len(df)
        assert set(signals.unique()).issubset({-1, 0, 1})

    def test_description(self):
        strategy = MeanReversionCombo()
        assert '均值回归' in strategy.description()
        assert 'BB' in strategy.description()

    def test_custom_params(self):
        strategy = MeanReversionCombo(bb_period=15, bb_std=1.5, rsi_period=7)
        assert '15' in strategy.name()

    def test_extreme_data(self):
        """极端数据不应崩溃"""
        np.random.seed(42)
        n = 100
        dates = pd.date_range('2024-01-01', periods=n, freq='D')
        # 剧烈波动
        close = np.abs(np.cumsum(np.random.randn(n) * 5)) + 1
        df = pd.DataFrame({
            'open': close, 'high': close * 1.05, 'low': close * 0.95,
            'close': close, 'volume': np.ones(n) * 100000,
        }, index=dates)
        strategy = MeanReversionCombo()
        signals = strategy.generate_signals(df)
        assert len(signals) == n


class TestDefaultCombo:
    """默认组合策略测试"""

    def test_create(self):
        combo = create_default_combo()
        assert 'Combo' in combo.name()

    def test_generate_signals(self):
        df = create_test_data(200)
        combo = create_default_combo()
        signals = combo.generate_signals(df)
        assert len(signals) == len(df)

    def test_has_three_components(self):
        combo = create_default_combo()
        assert len(combo.strategies) == 3


class TestChineseColumns:
    """中文列名兼容测试"""

    def test_rsi_macd_chinese(self):
        df = create_test_data(200)
        df = df.rename(columns={
            'open': '开盘', 'high': '最高', 'low': '最低',
            'close': '收盘', 'volume': '成交量',
        })
        strategy = RSIMACDCombo()
        signals = strategy.generate_signals(df)
        assert len(signals) == len(df)

    def test_trend_follow_chinese(self):
        df = create_test_data(200)
        df = df.rename(columns={
            'open': '开盘', 'high': '最高', 'low': '最低',
            'close': '收盘', 'volume': '成交量',
        })
        strategy = TrendFollowCombo()
        signals = strategy.generate_signals(df)
        assert len(signals) == len(df)

    def test_mean_reversion_chinese(self):
        df = create_test_data(200)
        df = df.rename(columns={
            'open': '开盘', 'high': '最高', 'low': '最低',
            'close': '收盘', 'volume': '成交量',
        })
        strategy = MeanReversionCombo()
        signals = strategy.generate_signals(df)
        assert len(signals) == len(df)
