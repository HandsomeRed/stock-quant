#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟交易模块单元测试
"""

import pytest
from datetime import datetime
from src.trading.simulated_account import (
    SimulatedAccount, Position, Order, Trade,
    OrderType, OrderStatus
)


class TestPosition:
    """持仓测试"""
    
    def test_position_creation(self):
        """测试持仓创建"""
        pos = Position(
            stock_code="000001",
            stock_name="平安银行",
            volume=1000,
            avg_price=10.0,
            current_price=10.5
        )
        
        assert pos.stock_code == "000001"
        assert pos.stock_name == "平安银行"
        assert pos.volume == 1000
        assert pos.avg_price == 10.0
        assert pos.current_price == 10.5
    
    def test_market_value(self):
        """测试市值计算"""
        pos = Position(
            stock_code="000001",
            stock_name="平安银行",
            volume=1000,
            avg_price=10.0,
            current_price=10.5
        )
        
        assert pos.market_value == 10500.0  # 1000 * 10.5
    
    def test_cost_value(self):
        """测试成本计算"""
        pos = Position(
            stock_code="000001",
            stock_name="平安银行",
            volume=1000,
            avg_price=10.0
        )
        
        assert pos.cost_value == 10000.0  # 1000 * 10.0
    
    def test_profit(self):
        """测试盈亏计算"""
        pos = Position(
            stock_code="000001",
            stock_name="平安银行",
            volume=1000,
            avg_price=10.0,
            current_price=10.5
        )
        
        assert pos.profit == 500.0  # 10500 - 10000
    
    def test_profit_rate(self):
        """测试盈亏比例"""
        pos = Position(
            stock_code="000001",
            stock_name="平安银行",
            volume=1000,
            avg_price=10.0,
            current_price=10.5
        )
        
        assert pos.profit_rate == 5.0  # 500 / 10000 * 100
    
    def test_profit_rate_zero_cost(self):
        """测试零成本时盈亏比例"""
        pos = Position(
            stock_code="000001",
            stock_name="平安银行",
            volume=1000,
            avg_price=0.0,
            current_price=10.0
        )
        
        assert pos.profit_rate == 0.0
    
    def test_position_to_dict(self):
        """测试持仓转字典"""
        pos = Position(
            stock_code="000001",
            stock_name="平安银行",
            volume=1000,
            avg_price=10.0,
            current_price=10.5
        )
        
        d = pos.to_dict()
        assert d['stock_code'] == "000001"
        assert d['market_value'] == 10500.0
        assert d['profit'] == 500.0
        assert d['profit_rate'] == "5.00%"


class TestOrder:
    """订单测试"""
    
    def test_order_creation(self):
        """测试订单创建"""
        order = Order(
            order_id="test123",
            stock_code="000001",
            stock_name="平安银行",
            order_type=OrderType.BUY,
            price=10.0,
            volume=1000
        )
        
        assert order.order_id == "test123"
        assert order.order_type == OrderType.BUY
        assert order.status == OrderStatus.PENDING
        assert order.amount == 10000.0
    
    def test_order_fill(self):
        """测试订单成交"""
        order = Order(
            order_id="test123",
            stock_code="000001",
            stock_name="平安银行",
            order_type=OrderType.BUY,
            price=10.0,
            volume=1000
        )
        
        order.fill(10.0, 1000)
        
        assert order.status == OrderStatus.FILLED
        assert order.fill_price == 10.0
        assert order.fill_volume == 1000
        assert order.fill_time is not None
    
    def test_order_cancel(self):
        """测试订单撤销"""
        order = Order(
            order_id="test123",
            stock_code="000001",
            stock_name="平安银行",
            order_type=OrderType.BUY,
            price=10.0,
            volume=1000
        )
        
        order.cancel()
        
        assert order.status == OrderStatus.CANCELLED


class TestSimulatedAccount:
    """模拟账户测试"""
    
    def test_account_initialization(self):
        """测试账户初始化"""
        account = SimulatedAccount(initial_capital=100000.0)
        
        assert account.initial_capital == 100000.0
        assert account.cash == 100000.0
        assert account.total_assets == 100000.0
        assert len(account.positions) == 0
        assert len(account.orders) == 0
        assert len(account.trades) == 0
    
    def test_buy_stock(self):
        """测试买入股票"""
        account = SimulatedAccount(initial_capital=100000.0)
        
        order = account.buy("000001", "平安银行", 10.0, 1000)
        
        assert order.status == OrderStatus.FILLED
        assert order.fill_price == 10.0
        assert order.fill_volume == 1000
        
        # 检查持仓
        assert "000001" in account.positions
        pos = account.positions["000001"]
        assert pos.volume == 1000
        assert pos.avg_price == 10.0
        
        # 检查资金（含手续费）
        commission = account.calculate_commission(10000.0, OrderType.BUY)
        expected_cash = 100000.0 - 10000.0 - commission
        assert abs(account.cash - expected_cash) < 0.01
    
    def test_sell_stock(self):
        """测试卖出股票"""
        account = SimulatedAccount(initial_capital=100000.0)
        
        # 先买入
        account.buy("000001", "平安银行", 10.0, 1000)
        
        # 再卖出
        order = account.sell("000001", "平安银行", 11.0, 1000)
        
        assert order.status == OrderStatus.FILLED
        assert order.fill_price == 11.0
        
        # 检查持仓已清空
        assert "000001" not in account.positions
        
        # 检查资金（卖出收入 - 手续费 - 印花税）
        commission = account.calculate_commission(11000.0, OrderType.SELL)
        expected_cash = 100000.0 - 10000.0 - 5.0 + 11000.0 - commission
        assert abs(account.cash - expected_cash) < 0.01
    
    def test_buy_insufficient_funds(self):
        """测试资金不足"""
        account = SimulatedAccount(initial_capital=10000.0)
        
        with pytest.raises(ValueError, match="资金不足"):
            account.buy("000001", "平安银行", 100.0, 1000)
    
    def test_sell_insufficient_position(self):
        """测试持仓不足"""
        account = SimulatedAccount(initial_capital=100000.0)
        account.buy("000001", "平安银行", 10.0, 1000)
        
        with pytest.raises(ValueError, match="持仓不足"):
            account.sell("000001", "平安银行", 11.0, 2000)
    
    def test_sell_no_position(self):
        """测试卖出未持有股票"""
        account = SimulatedAccount(initial_capital=100000.0)
        
        with pytest.raises(ValueError, match="不持有该股票"):
            account.sell("000001", "平安银行", 11.0, 1000)
    
    def test_buy_invalid_volume(self):
        """测试买入数量无效"""
        account = SimulatedAccount(initial_capital=100000.0)
        
        with pytest.raises(ValueError, match="100 的整数倍"):
            account.buy("000001", "平安银行", 10.0, 150)
    
    def test_commission_calculation(self):
        """测试手续费计算"""
        account = SimulatedAccount()
        
        # 买入：只有佣金
        amount = 10000.0
        commission = account.calculate_commission(amount, OrderType.BUY)
        expected = max(amount * 0.0003, 5.0)  # 万三，最低 5 元
        assert abs(commission - expected) < 0.01
        
        # 卖出：佣金 + 印花税
        commission_sell = account.calculate_commission(amount, OrderType.SELL)
        expected_sell = expected + amount * 0.001  # 加收千分之一印花税
        assert abs(commission_sell - expected_sell) < 0.01
    
    def test_min_commission(self):
        """测试最低手续费"""
        account = SimulatedAccount()
        
        # 小额交易，手续费不足 5 元按 5 元收
        commission = account.calculate_commission(1000.0, OrderType.BUY)
        assert commission == 5.0
    
    def test_account_summary(self):
        """测试账户概览"""
        account = SimulatedAccount(initial_capital=100000.0)
        account.buy("000001", "平安银行", 10.0, 1000)
        
        summary = account.get_account_summary()
        
        assert summary['initial_capital'] == 100000.0
        assert summary['position_count'] == 1
        assert summary['trade_count'] == 1
        assert 'total_assets' in summary
        assert 'total_profit' in summary
    
    def test_update_stock_price(self):
        """测试更新股票价格"""
        account = SimulatedAccount(initial_capital=100000.0)
        account.buy("000001", "平安银行", 10.0, 1000)
        
        # 更新股价
        account.update_stock_price("000001", 11.0)
        
        pos = account.positions["000001"]
        assert pos.current_price == 11.0
        assert pos.profit == 1000.0  # (11-10) * 1000
    
    def test_multiple_positions(self):
        """测试多个持仓"""
        account = SimulatedAccount(initial_capital=200000.0)
        
        account.buy("000001", "平安银行", 10.0, 1000)
        account.buy("600519", "贵州茅台", 1500.0, 100)
        
        assert len(account.positions) == 2
        assert "000001" in account.positions
        assert "600519" in account.positions
    
    def test_add_to_position(self):
        """测试加仓"""
        account = SimulatedAccount(initial_capital=200000.0)
        
        # 第一次买入
        account.buy("000001", "平安银行", 10.0, 1000)
        pos = account.positions["000001"]
        assert pos.volume == 1000
        assert pos.avg_price == 10.0
        
        # 第二次买入（加仓）
        account.buy("000001", "平安银行", 11.0, 1000)
        pos = account.positions["000001"]
        assert pos.volume == 2000
        assert pos.avg_price == 10.5  # (10*1000 + 11*1000) / 2000
    
    def test_partial_sell(self):
        """测试部分卖出"""
        account = SimulatedAccount(initial_capital=200000.0)
        
        # 买入 2000 股
        account.buy("000001", "平安银行", 10.0, 2000)
        
        # 卖出 1000 股
        account.sell("000001", "平安银行", 11.0, 1000)
        
        pos = account.positions["000001"]
        assert pos.volume == 1000  # 剩余 1000 股
    
    def test_get_orders(self):
        """测试获取订单列表"""
        account = SimulatedAccount(initial_capital=200000.0)
        
        account.buy("000001", "平安银行", 10.0, 1000)
        account.buy("600519", "贵州茅台", 1500.0, 100)
        
        orders = account.get_orders()
        assert len(orders) == 2
        
        filled_orders = account.get_orders(status=OrderStatus.FILLED)
        assert len(filled_orders) == 2
    
    def test_get_trades(self):
        """测试获取成交记录"""
        account = SimulatedAccount(initial_capital=200000.0)
        
        account.buy("000001", "平安银行", 10.0, 1000)
        account.sell("000001", "平安银行", 11.0, 500)
        
        trades = account.get_trades()
        assert len(trades) == 2
        
        # 检查成交记录内容
        buy_trade = trades[0]
        assert buy_trade.order_type == OrderType.BUY
        assert buy_trade.volume == 1000


class TestTrade:
    """成交记录测试"""
    
    def test_trade_creation(self):
        """测试成交记录创建"""
        trade = Trade(
            trade_id="t123",
            order_id="o123",
            stock_code="000001",
            stock_name="平安银行",
            order_type=OrderType.BUY,
            price=10.0,
            volume=1000,
            amount=10000.0,
            commission=5.0
        )
        
        assert trade.trade_id == "t123"
        assert trade.net_amount == 10005.0  # 买入：金额 + 手续费
    
    def test_sell_net_amount(self):
        """测试卖出净金额"""
        trade = Trade(
            trade_id="t123",
            order_id="o123",
            stock_code="000001",
            stock_name="平安银行",
            order_type=OrderType.SELL,
            price=11.0,
            volume=1000,
            amount=11000.0,
            commission=16.0  # 佣金 + 印花税
        )
        
        assert trade.net_amount == 10984.0  # 卖出：金额 - 手续费
