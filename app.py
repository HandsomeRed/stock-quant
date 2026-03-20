#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StockQuant - A 股量化交易平台
功能：股票数据查询、策略回测、模拟交易、学习记录
"""

import streamlit as st
import pandas as pd
import akshare as ak
from datetime import datetime
import sys
from pathlib import Path

# 导入模拟交易模块
sys.path.insert(0, str(Path(__file__).parent))
from src.trading.simulated_account import SimulatedAccount, OrderType

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# 页面配置
st.set_page_config(
    page_title="StockQuant - A 股量化交易平台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.title("📈 StockQuant")
    st.markdown("**A 股量化交易平台**")
    
    # 导航
    page = st.radio(
        "导航",
        ["🎯 股票查询", "📊 策略回测", "💼 模拟交易", "📚 学习记录"],
        index=0
    )
    
    st.markdown("---")
    
    # 快速统计
    st.markdown("### 📊 今日数据")
    try:
        stock_list = ak.stock_info_a_code_name()
        st.metric("A 股总数", f"{len(stock_list)}只")
    except:
        st.metric("A 股总数", "获取中...")
    
    # 知识库
    st.markdown("---")
    st.markdown("### 📚 知识库")
    kb_path = Path.home() / '.openclaw' / 'workspace' / 'knowledge-base' / 'quant-trading'
    if kb_path.exists():
        kb_files = list(kb_path.glob('*.md'))
        st.markdown(f"已沉淀 **{len(kb_files)}** 篇知识")

# ==================== 股票查询页面 ====================
if page == "🎯 股票查询":
    st.markdown('<h1 class="main-header">🎯 股票数据查询</h1>', unsafe_allow_html=True)
    st.markdown("查询 A 股股票历史行情、实时数据")
    st.markdown("---")
    
    # 输入区域
    col1, col2 = st.columns([3, 1])
    
    with col1:
        stock_code = st.text_input("股票代码", "000001", placeholder="输入 6 位股票代码")
    
    with col2:
        stock_name = ""
        try:
            stock_list = ak.stock_info_a_code_name()
            matched = stock_list[stock_list['code'] == stock_code]
            if not matched.empty:
                stock_name = matched.iloc[0]['name']
                st.info(f"股票名称：{stock_name}")
        except:
            pass
    
    # 日期选择
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("开始日期", value=datetime(2024, 1, 1))
    with col2:
        end_date = st.date_input("结束日期", value=datetime(2024, 12, 31))
    with col3:
        query_btn = st.button("🔍 查询数据", type="primary")
    
    # 查询并显示
    if query_btn and stock_code:
        with st.spinner(f"正在获取 {stock_code} 的数据..."):
            try:
                df = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period="daily",
                    start_date=start_date.strftime("%Y%m%d"),
                    end_date=end_date.strftime("%Y%m%d"),
                    adjust="qfq"
                )
                
                if not df.empty:
                    # 显示基本信息
                    st.success(f"✅ 获取成功！共 {len(df)} 条记录")
                    
                    # 关键指标
                    col1, col2, col3, col4 = st.columns(4)
                    latest = df.iloc[-1]
                    col1.metric("最新收盘价", f"{latest['收盘']:.2f}元")
                    col2.metric("期间最高", f"{df['最高'].max():.2f}元")
                    col3.metric("期间最低", f"{df['最低'].min():.2f}元")
                    
                    # 计算收益率
                    if len(df) > 1:
                        first_close = df.iloc[0]['收盘']
                        last_close = df.iloc[-1]['收盘']
                        change = ((last_close - first_close) / first_close) * 100
                        col4.metric("区间涨跌幅", f"{change:+.2f}%")
                    
                    # 数据表格
                    st.markdown("### 📊 历史数据")
                    st.dataframe(df[['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额']].tail(100))
                    
                    # 下载
                    csv = df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 下载 CSV",
                        data=csv,
                        file_name=f"{stock_code}_history.csv",
                        mime="text/csv"
                    )
                    
                    # K 线图（蜡烛图）
                    st.markdown("### 📈 K 线图（蜡烛图）")
                    
                    # 准备 K 线数据（最近 60 天）
                    kline_df = df.tail(60).reset_index(drop=True)
                    
                    # 使用 Plotly 绘制专业蜡烛图
                    import plotly.graph_objects as go
                    
                    fig = go.Figure(data=[go.Candlestick(
                        x=kline_df['日期'],
                        open=kline_df['开盘'],
                        high=kline_df['最高'],
                        low=kline_df['最低'],
                        close=kline_df['收盘'],
                        increasing_line_color='red',
                        decreasing_line_color='green',
                        name='K 线'
                    )])
                    
                    # 添加均线
                    if 'MA5' in kline_df.columns:
                        fig.add_trace(go.Scatter(
                            x=kline_df['日期'],
                            y=kline_df['MA5'],
                            line=dict(color='orange', width=1),
                            name='MA5'
                        ))
                    if 'MA10' in kline_df.columns:
                        fig.add_trace(go.Scatter(
                            x=kline_df['日期'],
                            y=kline_df['MA10'],
                            line=dict(color='blue', width=1),
                            name='MA10'
                        ))
                    
                    fig.update_layout(
                        height=500,
                        xaxis_title='日期',
                        yaxis_title='价格 (元)',
                        showlegend=True,
                        hovermode='x unified',
                        xaxis_rangeslider_visible=False,
                        template='plotly_white'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # K 线图说明
                    with st.expander("📖 K 线图说明"):
                        st.markdown("""
                        **蜡烛图组成：**
                        - 🔴 红色蜡烛（阳线）：收盘价 > 开盘价（上涨）
                        - 🟢 绿色蜡烛（阴线）：收盘价 < 开盘价（下跌）
                        - 蜡烛实体：开盘价与收盘价之间的部分
                        - 影线：最高价与最低价的细线
                        
                        **常见形态：**
                        - 大阳线：实体很长，表示强势上涨
                        - 大阴线：实体很长，表示强势下跌
                        - 十字星：开盘价≈收盘价，表示多空平衡
                        - 上影线长：上方压力大
                        - 下影线长：下方支撑强
                        """)
                    
                else:
                    st.warning("⚠️ 未找到数据，请检查股票代码或日期范围")
                    
            except Exception as e:
                st.error(f"❌ 获取数据失败：{str(e)}")
    
    # 热门股票快速查询
    st.markdown("---")
    st.markdown("### 🔥 热门股票快速查询")
    popular_stocks = [
        ("000001", "平安银行"),
        ("600519", "贵州茅台"),
        ("000858", "五粮液"),
        ("300750", "宁德时代"),
        ("000333", "美的集团"),
    ]
    
    cols = st.columns(5)
    for i, (code, name) in enumerate(popular_stocks):
        if cols[i].button(f"{code}\n{name}"):
            st.session_state['stock_code'] = code
            st.rerun()

# ==================== 策略回测页面 ====================
elif page == "📊 策略回测":
    st.markdown('<h1 class="main-header">📊 策略回测</h1>', unsafe_allow_html=True)
    st.markdown("在历史数据上验证交易策略")
    st.markdown("---")
    
    # 策略选择
    strategy = st.selectbox(
        "选择策略",
        ["双均线策略 (12/26)", "金叉死叉策略 (5/20)", "金叉死叉策略 (10/30)"]
    )
    
    # 股票选择
    stock_code = st.text_input("股票代码", "000001")
    
    # 回测参数
    col1, col2, col3 = st.columns(3)
    with col1:
        initial_capital = st.number_input("初始资金 (元)", value=100000, step=10000)
    with col2:
        start_date = st.date_input("开始日期", datetime(2024, 1, 1))
    with col3:
        end_date = st.date_input("结束日期", datetime(2024, 12, 31))
    
    if st.button("🚀 开始回测", type="primary"):
        with st.spinner("正在回测..."):
            # 这里调用回测引擎（简化版）
            st.info("💡 回测功能开发中... 将展示示例结果")
            
            # 示例结果
            st.markdown("### 📊 回测结果")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("总收益率", "+36.58%")
            col2.metric("年化收益率", "+38.35%")
            col3.metric("夏普比率", "1.25")
            col4.metric("最大回撤", "-12.12%")
            
            st.markdown("### 📈 资金曲线")
            # 模拟资金曲线数据
            import numpy as np
            days = 242
            curve = initial_capital * (1 + np.random.randn(days).cumsum() * 0.01)
            st.line_chart(curve)
            
            st.markdown("### 📝 交易记录")
            trades = pd.DataFrame({
                '日期': ['2024-03-15', '2024-06-20', '2024-09-10', '2024-12-25'],
                '类型': ['买入', '卖出', '买入', '卖出'],
                '价格': [9.50, 10.80, 10.50, 11.70],
                '数量': [10000, 10000, 10000, 10000],
                '金额': [95000, 108000, 105000, 117000]
            })
            st.dataframe(trades, hide_index=True)

# ==================== 模拟交易页面 ====================
elif page == "💼 模拟交易":
    st.markdown('<h1 class="main-header">💼 模拟交易</h1>', unsafe_allow_html=True)
    st.markdown("使用虚拟资金进行实盘模拟")
    st.markdown("---")
    
    # 初始化账户（使用 session_state 保持状态）
    if 'account' not in st.session_state:
        st.session_state.account = SimulatedAccount(initial_capital=100000.0)
    
    account = st.session_state.account
    
    # 账户信息
    st.markdown("### 📊 账户概览")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 可用资金", f"{account.cash:,.2f}元")
    col2.metric("📈 持仓市值", f"{account.total_market_value:,.2f}元")
    col3.metric("💵 总资产", f"{account.total_assets:,.2f}元")
    col4.metric("📊 浮动盈亏", f"{account.total_profit:+,.2f}元 ({account.total_profit_rate:+.2f}%)")
    
    st.markdown("---")
    
    # 交易操作
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🟢 买入")
        buy_stock = st.text_input("股票代码", "000001", key="buy")
        
        # 获取股票名称
        stock_name = ""
        try:
            stock_list = ak.stock_info_a_code_name()
            matched = stock_list[stock_list['code'] == buy_stock]
            if not matched.empty:
                stock_name = matched.iloc[0]['name']
                st.caption(f"股票名称：{stock_name}")
        except:
            pass
        
        buy_price = st.number_input("买入价格", min_value=0.01, step=0.01, key="buy_price")
        buy_volume = st.number_input("买入数量 (股)", min_value=100, step=100, value=1000, key="buy_vol")
        
        if st.button("🟢 买入", key="buy_btn", type="primary", use_container_width=True):
            try:
                order = account.buy(buy_stock, stock_name or buy_stock, buy_price, buy_volume)
                st.success(f"✅ 买入成交：{order.fill_volume}股 @ {order.fill_price:.2f}元")
                st.rerun()
            except ValueError as e:
                st.error(f"❌ {str(e)}")
    
    with col2:
        st.markdown("### 🔴 卖出")
        # 显示持仓供选择
        positions = account.get_positions()
        if positions:
            position_options = {f"{pos.stock_code} {pos.stock_name} ({pos.volume}股)": pos.stock_code for pos in positions}
            selected = st.selectbox("选择持仓", list(position_options.keys()))
            sell_stock_code = position_options[selected]
            sell_position = account.positions[sell_stock_code]
            
            sell_price = st.number_input("卖出价格", min_value=0.01, step=0.01, value=sell_position.current_price, key="sell_price")
            sell_volume = st.number_input("卖出数量 (股)", min_value=100, step=100, value=min(1000, sell_position.volume), key="sell_vol")
            
            if st.button("🔴 卖出", key="sell_btn", type="primary", use_container_width=True):
                try:
                    order = account.sell(sell_stock_code, sell_position.stock_name, sell_price, sell_volume)
                    st.success(f"✅ 卖出成交：{order.fill_volume}股 @ {order.fill_price:.2f}元")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ {str(e)}")
        else:
            st.info("暂无持仓，请先买入股票")
    
    st.markdown("---")
    
    # 持仓详情
    st.markdown("### 📊 持仓详情")
    positions = account.get_positions()
    if positions:
        pos_data = [pos.to_dict() for pos in positions]
        pos_df = pd.DataFrame(pos_data)
        
        # 格式化显示
        display_df = pos_df[['stock_code', 'stock_name', 'volume', 'avg_price', 'current_price', 'market_value', 'profit', 'profit_rate']].copy()
        display_df.columns = ['代码', '名称', '数量', '成本价', '当前价', '市值', '浮动盈亏', '盈亏比例']
        st.dataframe(display_df, hide_index=True, use_container_width=True)
    else:
        st.info("暂无持仓")
    
    st.markdown("---")
    
    # 成交记录
    st.markdown("### 📝 成交记录")
    trades = account.get_trades()
    if trades:
        trade_data = [trade.to_dict() for trade in trades[-20:]]  # 最近 20 条
        trade_df = pd.DataFrame(trade_data)
        
        display_trade_df = trade_df[['trade_time', 'order_type', 'stock_code', 'stock_name', 'price', 'volume', 'amount', 'commission']].copy()
        display_trade_df.columns = ['成交时间', '类型', '代码', '名称', '价格', '数量', '金额', '手续费']
        st.dataframe(display_trade_df, hide_index=True, use_container_width=True)
    else:
        st.info("暂无成交记录")

# ==================== 学习记录页面 ====================
elif page == "📚 学习记录":
    st.markdown('<h1 class="main-header">📚 学习记录</h1>', unsafe_allow_html=True)
    st.markdown("虾虾红的量化交易学习历程")
    st.markdown("---")
    
    # 统计概览
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📊 完成阶段", "4", "Stage 1/1b/2/3")
    col2.metric("✅ 测试通过", "54/55", "98% 通过率")
    col3.metric("📚 知识沉淀", "5 篇", "量化知识库")
    col4.metric("🏆 最佳策略", "+36.58%", "双均线 12/26")
    
    st.markdown("---")
    
    # 学习记录时间线
    st.markdown("### 📅 开发记录")
    
    st.markdown("""
    <div style="background: #f0f2f6; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #28a745;">
        <h3>🎯 Stage 3 - 模拟交易系统</h3>
        <p><strong>完成时间：</strong>2026-03-15 20:45</p>
        <p><strong>实现内容：</strong></p>
        <ul>
            <li>✅ 模拟账户管理（资金、持仓）</li>
            <li>✅ 买入/卖出委托下单</li>
            <li>✅ 持仓盈亏实时计算</li>
            <li>✅ 成交记录保存</li>
            <li>✅ 手续费计算（万三，最低 5 元）</li>
            <li>✅ 印花税（卖出千分之一）</li>
            <li>✅ 28 个单元测试，100% 通过率</li>
        </ul>
        <p><strong>核心功能：</strong></p>
        <ul>
            <li>初始资金：10 万元</li>
            <li>支持多股票持仓</li>
            <li>加仓自动计算平均成本</li>
            <li>部分卖出、全部卖出</li>
            <li>实时浮动盈亏展示</li>
        </ul>
    </div>
    
    <div style="background: #f0f2f6; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #1f77b4;">
        <h3>🎯 Stage 2 - 策略回测引擎</h3>
        <p><strong>完成时间：</strong>2026-03-12 20:00</p>
        <p><strong>实现内容：</strong></p>
        <ul>
            <li>✅ 策略基类接口</li>
            <li>✅ 均线交叉策略 (3 种)</li>
            <li>✅ 回测引擎 (含手续费、绩效分析)</li>
            <li>✅ 9 个单元测试，100% 通过率</li>
        </ul>
        <p><strong>回测结果（平安银行 2024）：</strong></p>
        <ul>
            <li>双均线 12/26：<strong>+36.58%</strong> ⭐</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: #f0f2f6; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #1f77b4;">
        <h3>📊 Stage 1b - 技术指标计算</h3>
        <p><strong>完成时间：</strong>2026-03-12 19:00</p>
        <p><strong>实现内容：</strong></p>
        <ul>
            <li>✅ K 线计算器</li>
            <li>✅ MA/EMA/MACD/RSI/布林带</li>
            <li>✅ 11 个单元测试，100% 通过率</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: #f0f2f6; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #1f77b4;">
        <h3>📡 Stage 1 - 数据获取</h3>
        <p><strong>完成时间：</strong>2026-03-12 18:30</p>
        <p><strong>实现内容：</strong></p>
        <ul>
            <li>✅ 数据获取模块</li>
            <li>✅ 获取 5489 只 A 股股票列表</li>
            <li>✅ 获取平安银行 2024 年历史数据 (242 条)</li>
            <li>✅ 6/7 测试通过</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # 明日计划
    st.markdown("---")
    st.markdown("### 🎯 明日计划 (Stage 3)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Stage 3 - 模拟交易**
        - [ ] 交易信号生成
        - [ ] 持仓管理
        - [ ] 盈亏计算
        - [ ] 模拟交易界面
        """)
    
    with col2:
        st.markdown("""
        **策略扩展**
        - [ ] RSI 策略实现
        - [ ] MACD 策略实现
        - [ ] 多股票批量回测
        - [ ] 策略参数优化
        """)

# 底部
st.markdown("---")
st.markdown(f"最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M')} | 🟢 平台运行中")
