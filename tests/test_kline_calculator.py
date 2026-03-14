#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K 线计算器单元测试
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 添加 src 目录到路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from data.kline_calculator import (
    calculate_ma,
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_bollinger_bands,
    calculate_all_indicators
)


@pytest.fixture
def sample_df():
    """创建示例数据"""
    return pd.DataFrame({
        '日期': pd.date_range('2024-01-01', periods=100),
        '收盘': np.random.uniform(10, 20, 100)
    })


class TestCalculateMA:
    """测试移动平均线计算"""
    
    def test_ma_columns_added(self, sample_df):
        """测试 MA 列是否添加"""
        result = calculate_ma(sample_df, periods=[5, 10, 20])
        
        assert 'MA5' in result.columns
        assert 'MA10' in result.columns
        assert 'MA20' in result.columns
    
    def test_ma_values_correct(self, sample_df):
        """测试 MA 值计算正确性"""
        result = calculate_ma(sample_df, periods=[5])
        
        # 手动计算 MA5
        expected = sample_df['收盘'].rolling(window=5).mean()
        
        pd.testing.assert_series_equal(result['MA5'], expected, check_names=False)
    
    def test_ma_initial_nan(self, sample_df):
        """测试 MA 初始值为 NaN"""
        result = calculate_ma(sample_df, periods=[5])
        
        # 前 4 个值应为 NaN
        assert result['MA5'].iloc[:4].isna().all()
        assert not pd.isna(result['MA5'].iloc[4])


class TestCalculateEMA:
    """测试指数移动平均线计算"""
    
    def test_ema_columns_added(self, sample_df):
        """测试 EMA 列是否添加"""
        result = calculate_ema(sample_df, periods=[12, 26])
        
        assert 'EMA12' in result.columns
        assert 'EMA26' in result.columns


class TestCalculateMACD:
    """测试 MACD 指标计算"""
    
    def test_macd_columns_added(self, sample_df):
        """测试 MACD 列是否添加"""
        result = calculate_macd(sample_df)
        
        assert 'MACD' in result.columns
        assert 'Signal' in result.columns
        assert 'MACD_Hist' in result.columns
    
    def test_macd_hist_formula(self, sample_df):
        """测试 MACD 柱状图公式"""
        result = calculate_macd(sample_df)
        
        # MACD_Hist = MACD - Signal
        expected = result['MACD'] - result['Signal']
        pd.testing.assert_series_equal(result['MACD_Hist'], expected, check_names=False)


class TestCalculateRSI:
    """测试 RSI 指标计算"""
    
    def test_rsi_column_added(self, sample_df):
        """测试 RSI 列是否添加"""
        result = calculate_rsi(sample_df, period=14)
        
        assert 'RSI' in result.columns
    
    def test_rsi_range(self, sample_df):
        """测试 RSI 值范围 (0-100)"""
        result = calculate_rsi(sample_df, period=14)
        
        # RSI 应在 0-100 之间（允许浮点误差）
        rsi_values = result['RSI'].dropna()
        assert (rsi_values >= 0).all()
        assert (rsi_values <= 100).all()


class TestCalculateBollingerBands:
    """测试布林带计算"""
    
    def test_bb_columns_added(self, sample_df):
        """测试布林带列是否添加"""
        result = calculate_bollinger_bands(sample_df, period=20)
        
        assert 'BB_Middle' in result.columns
        assert 'BB_Upper' in result.columns
        assert 'BB_Lower' in result.columns
    
    def test_bb_relationship(self, sample_df):
        """测试布林带关系 (上轨 > 中轨 > 下轨)"""
        result = calculate_bollinger_bands(sample_df, period=20)
        
        # 去掉 NaN 值
        valid = result.dropna()
        
        if len(valid) > 0:
            assert (valid['BB_Upper'] >= valid['BB_Middle']).all()
            assert (valid['BB_Middle'] >= valid['BB_Lower']).all()


class TestCalculateAllIndicators:
    """测试全部指标计算"""
    
    def test_all_indicators(self, sample_df):
        """测试一次性计算所有指标"""
        result = calculate_all_indicators(sample_df)
        
        # 检查所有指标列
        expected_columns = [
            'MA5', 'MA10', 'MA20', 'MA60',
            'EMA12', 'EMA26',
            'MACD', 'Signal', 'MACD_Hist',
            'RSI',
            'BB_Middle', 'BB_Upper', 'BB_Lower'
        ]
        
        for col in expected_columns:
            assert col in result.columns, f"缺少列：{col}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
