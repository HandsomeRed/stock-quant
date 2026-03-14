#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测演示 - 测试均线策略
"""

import sys
from pathlib import Path

# 添加路径
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

import akshare as ak
from strategy.ma_cross import MACrossStrategy, DualMAStrategy
from strategy.backtester import Backtester


def run_backtest(symbol: str = "000001", 
                 start_date: str = "20240101",
                 end_date: str = "20241231"):
    """运行回测"""
    
    print("=" * 70)
    print(f"📊 策略回测 - {symbol}")
    print("=" * 70)
    print()
    
    # 获取数据
    print("【步骤 1】获取历史数据...")
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq"
    )
    print(f"✅ 获取 {len(df)} 条记录")
    print()
    
    # 初始化回测引擎
    backtester = Backtester(initial_capital=100000, commission_rate=0.0003)
    
    # 策略列表
    strategies = [
        MACrossStrategy(short_period=5, long_period=20),
        MACrossStrategy(short_period=10, long_period=30),
        DualMAStrategy(fast_period=12, slow_period=26),
    ]
    
    results = []
    
    for strategy in strategies:
        print(f"【回测】{strategy.name()}")
        print("-" * 70)
        
        # 运行回测
        result = backtester.run(df, strategy)
        
        # 分析结果
        metrics = backtester.analyze(result, df)
        
        print(f"策略：{result['strategy']}")
        print(f"初始资金：{result['initial_capital']:,.0f} 元")
        print(f"最终价值：{metrics['最终价值']}")
        print(f"总收益率：{metrics['总收益率']}")
        print(f"年化收益率：{metrics['年化收益率']}")
        print(f"夏普比率：{metrics['夏普比率']}")
        print(f"最大回撤：{metrics['最大回撤']}")
        print(f"交易次数：{metrics['交易次数']}")
        print(f"胜率：{metrics['胜率']}")
        print()
        
        results.append({
            'strategy': strategy.name(),
            'result': result,
            'metrics': metrics
        })
    
    # 汇总对比
    print("=" * 70)
    print("📋 策略对比")
    print("=" * 70)
    print(f"{'策略':<25} {'收益率':<12} {'夏普比率':<10} {'最大回撤':<12} {'交易次数':<8}")
    print("-" * 70)
    
    for r in results:
        m = r['metrics']
        print(f"{r['strategy']:<25} {m['总收益率']:<12} {m['夏普比率']:<10} {m['最大回撤']:<12} {m['交易次数']:<8}")
    
    print("=" * 70)
    
    # 最佳策略
    best = max(results, key=lambda x: float(x['metrics']['总收益率'].replace('%', '')))
    print(f"\n🏆 最佳策略：{best['strategy']}")
    print(f"   收益率：{best['metrics']['总收益率']}")
    print(f"   夏普比率：{best['metrics']['夏普比率']}")
    
    return results


if __name__ == "__main__":
    run_backtest("000001", "20240101", "20241231")
