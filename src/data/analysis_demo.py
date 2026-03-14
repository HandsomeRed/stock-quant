#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据分析演示

整合数据获取 + 技术指标 + 基础分析
"""

import akshare as ak
import pandas as pd
from datetime import datetime
from pathlib import Path

# 导入本地模块
from kline_calculator import calculate_all_indicators


def analyze_stock(symbol: str = "000001", 
                  start_date: str = "20240101",
                  end_date: str = "20241231"):
    """
    完整股票分析流程
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        分析结果字典
    """
    print("=" * 70)
    print(f"📊 股票分析报告 - {symbol}")
    print("=" * 70)
    print()
    
    # 1. 获取历史数据
    print("【步骤 1】获取历史数据...")
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq"
    )
    print(f"✅ 获取 {len(df)} 条记录 ({df['日期'].min()} ~ {df['日期'].max()})")
    print()
    
    # 2. 计算技术指标
    print("【步骤 2】计算技术指标...")
    df = calculate_all_indicators(df)
    print("✅ 指标计算完成：MA, EMA, MACD, RSI, 布林带")
    print()
    
    # 3. 基础统计
    print("【步骤 3】基础统计分析")
    print("-" * 70)
    
    latest = df.iloc[-1]
    period_start = df.iloc[0]
    
    # 价格统计
    print(f"📈 价格统计:")
    print(f"   期初收盘价：{period_start['收盘']:.2f} 元")
    print(f"   期末收盘价：{latest['收盘']:.2f} 元")
    print(f"   期间最高价：{df['最高'].max():.2f} 元")
    print(f"   期间最低价：{df['最低'].min():.2f} 元")
    
    # 收益率
    total_return = (latest['收盘'] - period_start['收盘']) / period_start['收盘'] * 100
    print(f"   期间总收益率：{total_return:+.2f}%")
    print()
    
    # 4. 技术指标信号
    print("📊 技术指标信号 (最新交易日)")
    print("-" * 70)
    
    # MA 信号
    if latest['收盘'] > latest['MA5'] > latest['MA10'] > latest['MA20']:
        ma_signal = "✅ 多头排列"
    elif latest['收盘'] < latest['MA5'] < latest['MA10'] < latest['MA20']:
        ma_signal = "❌ 空头排列"
    else:
        ma_signal = "➖ 震荡整理"
    print(f"   均线系统：{ma_signal}")
    print(f"      收盘价：{latest['收盘']:.2f}")
    print(f"      MA5: {latest['MA5']:.2f} | MA10: {latest['MA10']:.2f} | MA20: {latest['MA20']:.2f}")
    print()
    
    # MACD 信号
    if latest['MACD'] > latest['Signal'] and latest['MACD_Hist'] > 0:
        macd_signal = "✅ 金叉 (看涨)"
    elif latest['MACD'] < latest['Signal'] and latest['MACD_Hist'] < 0:
        macd_signal = "❌ 死叉 (看跌)"
    else:
        macd_signal = "➖ 粘合震荡"
    print(f"   MACD: {macd_signal}")
    print(f"      MACD: {latest['MACD']:.4f} | Signal: {latest['Signal']:.4f} | Hist: {latest['MACD_Hist']:.4f}")
    print()
    
    # RSI 信号
    rsi = latest['RSI']
    if rsi > 70:
        rsi_signal = "⚠️ 超买区 (>70)"
    elif rsi < 30:
        rsi_signal = "✅ 超卖区 (<30)"
    else:
        rsi_signal = "➖ 中性区"
    print(f"   RSI: {rsi_signal}")
    print(f"      RSI(14): {rsi:.2f}")
    print()
    
    # 布林带信号
    if latest['收盘'] > latest['BB_Upper']:
        bb_signal = "⚠️ 突破上轨 (可能回调)"
    elif latest['收盘'] < latest['BB_Lower']:
        bb_signal = "✅ 突破下轨 (可能反弹)"
    else:
        bb_signal = "➖ 布林带内震荡"
    print(f"   布林带：{bb_signal}")
    print(f"      上轨：{latest['BB_Upper']:.2f} | 中轨：{latest['BB_Middle']:.2f} | 下轨：{latest['BB_Lower']:.2f}")
    print()
    
    # 5. 综合评分
    print("📋 综合评分")
    print("-" * 70)
    
    score = 50  # 基础分
    
    # MA 评分
    if "多头" in ma_signal:
        score += 15
    elif "空头" in ma_signal:
        score -= 15
    
    # MACD 评分
    if "金叉" in macd_signal:
        score += 15
    elif "死叉" in macd_signal:
        score -= 15
    
    # RSI 评分
    if rsi < 30:
        score += 10
    elif rsi > 70:
        score -= 10
    
    # 趋势评分
    if total_return > 0:
        score += 5
    else:
        score -= 5
    
    # 限制分数范围
    score = max(0, min(100, score))
    
    print(f"   综合得分：{score}/100")
    
    if score >= 70:
        rating = "✅ 强烈推荐"
    elif score >= 55:
        rating = "👍 推荐"
    elif score >= 40:
        rating = "➖ 观望"
    elif score >= 25:
        rating = "👎 谨慎"
    else:
        rating = "❌ 回避"
    
    print(f"   评级：{rating}")
    print()
    
    # 6. 保存数据
    print("【步骤 4】保存分析数据...")
    data_dir = Path(__file__).parent.parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # 保存完整数据
    output_file = data_dir / f"{symbol}_analysis.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ 数据已保存：{output_file}")
    print()
    
    print("=" * 70)
    print("✅ 分析完成！")
    print("=" * 70)
    
    return {
        'symbol': symbol,
        'score': score,
        'rating': rating,
        'total_return': total_return,
        'latest_price': latest['收盘'],
        'rsi': rsi,
        'ma_signal': ma_signal,
        'macd_signal': macd_signal,
        'bb_signal': bb_signal
    }


def main():
    """主函数 - 分析多只股票"""
    
    # 分析股票列表
    stocks_to_analyze = [
        ("000001", "平安银行"),
        ("600519", "贵州茅台"),
        ("000858", "五粮液"),
    ]
    
    results = []
    
    for symbol, name in stocks_to_analyze:
        try:
            result = analyze_stock(symbol)
            results.append(result)
            print("\n\n")
        except Exception as e:
            print(f"❌ {symbol} 分析失败：{e}\n\n")
    
    # 汇总报告
    if results:
        print("=" * 70)
        print("📊 股票分析汇总报告")
        print("=" * 70)
        print(f"{'股票代码':<10} {'股票名称':<10} {'得分':<8} {'评级':<10} {'收益率':<12}")
        print("-" * 70)
        
        for r in results:
            print(f"{r['symbol']:<10} {r['rating']:<10} {r['score']:<8} {r['rating']:<10} {r['total_return']:>+10.2f}%")
        
        print("=" * 70)


if __name__ == "__main__":
    main()
