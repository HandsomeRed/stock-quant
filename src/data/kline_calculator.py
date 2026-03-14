#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K 线数据计算模块

功能：
- 计算移动平均线 (MA/EMA)
- 计算 MACD 指标
- 计算 RSI 指标
- 计算布林带
"""

import pandas as pd
import numpy as np


def calculate_ma(df: pd.DataFrame, periods: list = [5, 10, 20, 60]) -> pd.DataFrame:
    """
    计算移动平均线
    
    Args:
        df: 包含'收盘'列的 DataFrame
        periods: 均线周期列表
        
    Returns:
        添加了 MA 列的 DataFrame
    """
    df = df.copy()
    
    for period in periods:
        df[f'MA{period}'] = df['收盘'].rolling(window=period).mean()
    
    return df


def calculate_ema(df: pd.DataFrame, periods: list = [12, 26]) -> pd.DataFrame:
    """
    计算指数移动平均线
    
    Args:
        df: 包含'收盘'列的 DataFrame
        periods: EMA 周期列表
        
    Returns:
        添加了 EMA 列的 DataFrame
    """
    df = df.copy()
    
    for period in periods:
        df[f'EMA{period}'] = df['收盘'].ewm(span=period, adjust=False).mean()
    
    return df


def calculate_macd(df: pd.DataFrame, 
                   fast: int = 12, 
                   slow: int = 26, 
                   signal: int = 9) -> pd.DataFrame:
    """
    计算 MACD 指标
    
    Args:
        df: 包含'收盘'列的 DataFrame
        fast: 快线周期
        slow: 慢线周期
        signal: 信号线周期
        
    Returns:
        添加了 MACD 列的 DataFrame
    """
    df = df.copy()
    
    # 计算 EMA
    ema_fast = df['收盘'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['收盘'].ewm(span=slow, adjust=False).mean()
    
    # MACD 线 = 快线 EMA - 慢线 EMA
    df['MACD'] = ema_fast - ema_slow
    
    # 信号线 = MACD 的 EMA
    df['Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
    
    # MACD 柱状图
    df['MACD_Hist'] = df['MACD'] - df['Signal']
    
    return df


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    计算 RSI 相对强弱指标
    
    Args:
        df: 包含'收盘'列的 DataFrame
        period: RSI 周期
        
    Returns:
        添加了 RSI 列的 DataFrame
    """
    df = df.copy()
    
    # 计算价格变化
    delta = df['收盘'].diff()
    
    # 分离上涨和下跌
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # 计算平均涨幅和跌幅
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # 计算 RS 和 RSI
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df


def calculate_bollinger_bands(df: pd.DataFrame, 
                               period: int = 20, 
                               std_dev: float = 2.0) -> pd.DataFrame:
    """
    计算布林带
    
    Args:
        df: 包含'收盘'列的 DataFrame
        period: 周期
        std_dev: 标准差倍数
        
    Returns:
        添加了布林带列的 DataFrame
    """
    df = df.copy()
    
    # 中轨 = MA
    df['BB_Middle'] = df['收盘'].rolling(window=period).mean()
    
    # 标准差
    std = df['收盘'].rolling(window=period).std()
    
    # 上轨和下轨
    df['BB_Upper'] = df['BB_Middle'] + (std_dev * std)
    df['BB_Lower'] = df['BB_Middle'] - (std_dev * std)
    
    return df


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算所有技术指标
    
    Args:
        df: 包含'收盘'列的 DataFrame
        
    Returns:
        添加了所有技术指标的 DataFrame
    """
    df = calculate_ma(df)
    df = calculate_ema(df)
    df = calculate_macd(df)
    df = calculate_rsi(df)
    df = calculate_bollinger_bands(df)
    
    return df


if __name__ == "__main__":
    # 测试代码
    import akshare as ak
    
    # 获取测试数据
    print("📊 获取测试数据...")
    df = ak.stock_zh_a_hist(
        symbol="000001",
        period="daily",
        start_date="20240101",
        end_date="20241231"
    )
    
    print(f"原始数据：{len(df)} 条记录")
    
    # 计算所有指标
    print("📈 计算技术指标...")
    df = calculate_all_indicators(df)
    
    print(f"\n数据列：{list(df.columns)}")
    print(f"\n最后 5 条记录：")
    print(df[['日期', '收盘', 'MA5', 'MA20', 'MACD', 'RSI', 'BB_Upper', 'BB_Lower']].tail())
    
    # 检查信号
    latest = df.iloc[-1]
    print(f"\n📊 最新信号 (2024-12-31):")
    print(f"   收盘价：{latest['收盘']:.2f}")
    print(f"   MA5: {latest['MA5']:.2f}")
    print(f"   MA20: {latest['MA20']:.2f}")
    print(f"   RSI: {latest['RSI']:.2f}")
    
    if latest['RSI'] > 70:
        print("   ⚠️ RSI 超买 (>70)")
    elif latest['RSI'] < 30:
        print("   ✅ RSI 超卖 (<30)")
    else:
        print("   ➖ RSI 中性")
