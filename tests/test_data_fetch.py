#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据获取模块单元测试
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# 添加 src 目录到路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from data.fetch_stock_data import (
    fetch_stock_history,
    fetch_realtime_quotes,
    fetch_stock_list,
    save_to_csv
)


class TestFetchStockHistory:
    """测试股票历史数据获取"""
    
    def test_fetch_single_stock(self):
        """测试获取单只股票历史数据"""
        df = fetch_stock_history(
            symbol="000001",
            start_date="20240101",
            end_date="20240131",
            period="daily"
        )
        
        assert not df.empty, "数据不应为空"
        assert len(df) > 0, "至少应有一条记录"
        assert "日期" in df.columns, "应包含日期列"
        assert "收盘" in df.columns, "应包含收盘价列"
        assert "开盘" in df.columns, "应包含开盘价列"
        assert "最高" in df.columns, "应包含最高价列"
        assert "最低" in df.columns, "应包含最低价列"
    
    def test_date_range(self):
        """测试日期范围正确性"""
        df = fetch_stock_history(
            symbol="000001",
            start_date="20240101",
            end_date="20240131",
            period="daily"
        )
        
        # 验证日期在指定范围内
        min_date = pd.to_datetime(df["日期"].min())
        max_date = pd.to_datetime(df["日期"].max())
        
        assert min_date >= pd.to_datetime("2024-01-01"), "最小日期不应早于开始日期"
        assert max_date <= pd.to_datetime("2024-01-31"), "最大日期不应晚于结束日期"
    
    def test_price_validity(self):
        """测试价格数据有效性"""
        df = fetch_stock_history(
            symbol="000001",
            start_date="20240101",
            end_date="20240131",
            period="daily"
        )
        
        # 价格应为正数
        assert (df["收盘"] > 0).all(), "收盘价应全部为正数"
        assert (df["开盘"] > 0).all(), "开盘价应全部为正数"
        
        # 最高价应 >= 最低价
        assert (df["最高"] >= df["最低"]).all(), "最高价应大于等于最低价"


class TestFetchStockList:
    """测试股票列表获取"""
    
    def test_fetch_stock_list(self):
        """测试获取 A 股股票列表"""
        df = fetch_stock_list()
        
        assert not df.empty, "股票列表不应为空"
        assert len(df) > 0, "至少应有一只股票"
        assert "code" in df.columns, "应包含股票代码列"
        assert "name" in df.columns, "应包含股票名称列"
    
    def test_stock_code_format(self):
        """测试股票代码格式"""
        df = fetch_stock_list()
        
        # 股票代码应为 6 位数字
        sample_codes = df["code"].head(10).tolist()
        for code in sample_codes:
            assert len(str(code)) == 6, f"股票代码 {code} 应为 6 位"
            assert str(code).isdigit(), f"股票代码 {code} 应全为数字"


class TestSaveToCSV:
    """测试 CSV 保存功能"""
    
    def test_save_dataframe(self, tmp_path):
        """测试保存 DataFrame 到 CSV"""
        df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "收盘": [10.5, 10.8],
            "成交量": [1000, 1200]
        })
        
        save_to_csv(df, "test_data.csv", data_dir=str(tmp_path))
        
        # 验证文件已创建
        filepath = tmp_path / "test_data.csv"
        assert filepath.exists(), "CSV 文件应已创建"
        
        # 验证数据正确性
        loaded_df = pd.read_csv(filepath)
        assert len(loaded_df) == 2, "加载的数据应有 2 条记录"
        assert list(loaded_df.columns) == ["日期", "收盘", "成交量"], "列名应匹配"


class TestRealtimeQuotes:
    """测试实时行情获取"""
    
    def test_fetch_realtime(self):
        """测试获取实时行情"""
        df = fetch_realtime_quotes()
        
        assert not df.empty, "实时行情不应为空"
        assert len(df) > 0, "至少应有一只股票行情"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
