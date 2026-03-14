#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 股数据获取模块 - Stage 1

功能：
- 获取股票历史数据（日 K/分钟 K）
- 获取实时行情
- 获取股票列表
- 数据清洗与存储
"""

import akshare as ak
import pandas as pd
from datetime import datetime
from pathlib import Path


def fetch_stock_history(symbol: str = "000001", 
                        start_date: str = "20240101", 
                        end_date: str = "20241231",
                        period: str = "daily") -> pd.DataFrame:
    """
    获取 A 股股票历史行情数据
    
    Args:
        symbol: 股票代码，如 "000001" (平安银行)
        start_date: 开始日期，格式 "YYYYMMDD"
        end_date: 结束日期，格式 "YYYYMMDD"
        period: 周期类型，daily/weekly/monthly
        
    Returns:
        DataFrame 包含历史行情数据
    """
    print(f"📊 获取股票 {symbol} 历史数据 ({start_date} - {end_date})...")
    
    try:
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"  # 前复权
        )
        
        print(f"✅ 成功获取 {len(df)} 条记录")
        print(f"📈 数据列：{list(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"❌ 获取数据失败：{e}")
        return pd.DataFrame()


def fetch_realtime_quotes() -> pd.DataFrame:
    """
    获取 A 股实时行情（所有股票）
    
    Returns:
        DataFrame 包含实时行情数据
    """
    print("📡 获取 A 股实时行情...")
    
    try:
        df = ak.stock_zh_a_spot_em()
        print(f"✅ 成功获取 {len(df)} 只股票实时行情")
        
        return df
        
    except Exception as e:
        print(f"❌ 获取实时行情失败：{e}")
        return pd.DataFrame()


def fetch_stock_list() -> pd.DataFrame:
    """
    获取 A 股股票列表
    
    Returns:
        DataFrame 包含股票代码和名称
    """
    print("📋 获取 A 股股票列表...")
    
    try:
        df = ak.stock_info_a_code_name()
        print(f"✅ 成功获取 {len(df)} 只股票信息")
        
        return df
        
    except Exception as e:
        print(f"❌ 获取股票列表失败：{e}")
        return pd.DataFrame()


def save_to_csv(df: pd.DataFrame, filename: str, data_dir: str = "data"):
    """
    保存 DataFrame 到 CSV 文件
    
    Args:
        df: 要保存的 DataFrame
        filename: 文件名
        data_dir: 数据目录
    """
    data_path = Path(__file__).parent.parent.parent / data_dir
    data_path.mkdir(exist_ok=True)
    
    filepath = data_path / filename
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"💾 数据已保存到：{filepath}")


def main():
    """主函数 - 演示数据获取流程"""
    print("=" * 60)
    print("🚀 A 股量化助手 - 数据获取演示")
    print("=" * 60)
    print()
    
    # 1. 获取股票列表
    print("【步骤 1】获取股票列表")
    stock_list = fetch_stock_list()
    if not stock_list.empty:
        print(stock_list.head(10))
        save_to_csv(stock_list, "stock_list.csv")
    print()
    
    # 2. 获取单只股票历史数据
    print("【步骤 2】获取平安银行 (000001) 历史数据")
    history = fetch_stock_history(
        symbol="000001",
        start_date="20240101",
        end_date="20241231",
        period="daily"
    )
    if not history.empty:
        print(history.head(10))
        print(f"\n📊 数据概览：")
        print(f"   记录数：{len(history)}")
        print(f"   日期范围：{history['日期'].min()} - {history['日期'].max()}")
        print(f"   收盘价范围：{history['收盘'].min():.2f} - {history['收盘'].max():.2f}")
        save_to_csv(history, "000001_history.csv")
    print()
    
    # 3. 获取实时行情（可选，数据量大）
    # print("【步骤 3】获取实时行情")
    # realtime = fetch_realtime_quotes()
    # if not realtime.empty:
    #     print(realtime.head(10))
    # print()
    
    print("=" * 60)
    print("✅ 数据获取完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
