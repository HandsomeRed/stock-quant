#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险管理模块测试 - Stage 3.5
"""

import pytest
import numpy as np
from src.trading.risk_manager import (
    RiskConfig,
    RiskManager,
    PositionInfo,
)


class TestRiskConfig:
    """风险配置测试"""
    
    def test_default_config(self):
        config = RiskConfig()
        assert config.max_position_pct == 0.3
        assert config.stop_loss_pct == 0.08
        assert config.take_profit_pct == 0.20
    
    def test_custom_config(self):
        config = RiskConfig(max_position_pct=0.5, stop_loss_pct=0.1)
        assert config.max_position_pct == 0.5
        assert config.stop_loss_pct == 0.1


class TestPositionInfo:
    """持仓信息测试"""
    
    def test_market_value(self):
        pos = PositionInfo(symbol='000001', shares=100, avg_cost=10.0, current_price=12.0)
        assert pos.market_value == 1200.0
    
    def test_pnl(self):
        pos = PositionInfo(symbol='000001', shares=100, avg_cost=10.0, current_price=12.0)
        assert pos.pnl == 200.0
    
    def test_pnl_pct(self):
        pos = PositionInfo(symbol='000001', shares=100, avg_cost=10.0, current_price=12.0)
        assert abs(pos.pnl_pct - 0.2) < 0.001
    
    def test_pnl_pct_zero_cost(self):
        pos = PositionInfo(symbol='000001', shares=0, avg_cost=0, current_price=12.0)
        assert pos.pnl_pct == 0.0
    
    def test_drawdown_from_high(self):
        pos = PositionInfo(symbol='000001', shares=100, avg_cost=10.0, current_price=9.0, highest_price=12.0)
        assert abs(pos.drawdown_from_high - 0.25) < 0.001
    
    def test_drawdown_from_high_zero(self):
        pos = PositionInfo(symbol='000001', shares=100, avg_cost=10.0, current_price=10.0, highest_price=0)
        assert pos.drawdown_from_high == 0.0


class TestRiskManager:
    """风险管理器测试"""
    
    def setup_method(self):
        self.rm = RiskManager(initial_capital=100000)
    
    # ==================== 初始化测试 ====================
    
    def test_initial_state(self):
        assert self.rm.total_value == 100000
        assert self.rm.cash == 100000
        assert self.rm.exposure_pct == 0.0
        assert len(self.rm.positions) == 0
    
    def test_custom_config(self):
        config = RiskConfig(stop_loss_pct=0.05)
        rm = RiskManager(config=config)
        assert rm.config.stop_loss_pct == 0.05
    
    # ==================== 仓位计算测试 ====================
    
    def test_calculate_position_size(self):
        shares = self.rm.calculate_position_size('000001', 10.0)
        assert shares > 0
        assert shares % 100 == 0  # A股按手
        assert shares * 10.0 <= 100000 * 0.3  # 不超过最大仓位
    
    def test_position_size_zero_price(self):
        shares = self.rm.calculate_position_size('000001', 0)
        assert shares == 0
    
    def test_position_size_when_locked(self):
        self.rm.is_risk_locked = True
        shares = self.rm.calculate_position_size('000001', 10.0)
        assert shares == 0
    
    def test_position_size_signal_strength(self):
        full = self.rm.calculate_position_size('000001', 10.0, signal_strength=1.0)
        half = self.rm.calculate_position_size('000001', 10.0, signal_strength=0.5)
        assert full >= half
    
    # ==================== 凯利公式测试 ====================
    
    def test_kelly_positive(self):
        # 60%胜率，盈亏比2:1 → 正凯利
        kelly = self.rm.calculate_kelly_size(0.6, 0.10, 0.05)
        assert kelly > 0
        assert kelly <= self.rm.config.max_position_pct
    
    def test_kelly_negative(self):
        # 30%胜率，盈亏比1:1 → 负凯利 → 返回0
        kelly = self.rm.calculate_kelly_size(0.3, 0.05, 0.05)
        assert kelly == 0
    
    def test_kelly_edge_cases(self):
        assert self.rm.calculate_kelly_size(0, 0.1, 0.1) == 0
        assert self.rm.calculate_kelly_size(1, 0.1, 0.1) == 0
        assert self.rm.calculate_kelly_size(0.5, 0.1, 0) == 0
    
    # ==================== 开仓平仓测试 ====================
    
    def test_open_position(self):
        success, msg = self.rm.open_position('000001', 1000, 10.0)
        assert success
        assert '000001' in self.rm.positions
        assert self.rm.cash == 90000
        assert self.rm.positions['000001'].shares == 1000
    
    def test_open_position_insufficient_cash(self):
        success, msg = self.rm.open_position('000001', 100000, 10.0)
        assert not success
        assert '不足' in msg
    
    def test_add_to_position(self):
        self.rm.open_position('000001', 1000, 10.0)
        self.rm.open_position('000001', 500, 12.0)
        pos = self.rm.positions['000001']
        assert pos.shares == 1500
        expected_cost = (1000 * 10.0 + 500 * 12.0) / 1500
        assert abs(pos.avg_cost - expected_cost) < 0.01
    
    def test_close_position(self):
        self.rm.open_position('000001', 1000, 10.0)
        success, msg = self.rm.close_position('000001', price=12.0)
        assert success
        assert '000001' not in self.rm.positions
        assert self.rm.cash == 90000 + 1000 * 12.0
    
    def test_close_partial(self):
        self.rm.open_position('000001', 1000, 10.0)
        self.rm.close_position('000001', shares=500, price=12.0)
        assert self.rm.positions['000001'].shares == 500
    
    def test_close_nonexistent(self):
        success, msg = self.rm.close_position('999999', price=10.0)
        assert not success
    
    def test_trade_history(self):
        self.rm.open_position('000001', 1000, 10.0)
        self.rm.close_position('000001', price=12.0)
        assert len(self.rm.trade_history) == 2
        assert self.rm.trade_history[0]['action'] == 'buy'
        assert self.rm.trade_history[1]['action'] == 'sell'
        assert self.rm.trade_history[1]['pnl'] == 2000.0
    
    # ==================== 止损止盈测试 ====================
    
    def test_stop_loss_triggered(self):
        self.rm.open_position('000001', 1000, 10.0)
        self.rm.positions['000001'].current_price = 9.0  # -10%
        triggered, msg = self.rm.check_stop_loss('000001')
        assert triggered
        assert '止损' in msg
    
    def test_stop_loss_not_triggered(self):
        self.rm.open_position('000001', 1000, 10.0)
        self.rm.positions['000001'].current_price = 9.7  # -3%, below stop_loss(8%) and trailing(5%)
        triggered, _ = self.rm.check_stop_loss('000001')
        assert not triggered
    
    def test_trailing_stop(self):
        self.rm.open_position('000001', 1000, 10.0)
        pos = self.rm.positions['000001']
        pos.highest_price = 15.0
        pos.current_price = 14.0  # 从高点回落 6.7%
        # trailing stop at 5%: 14/15 = 0.933, dd = 6.7% > 5% → triggered
        triggered, msg = self.rm.check_stop_loss('000001')
        assert triggered
        assert '移动止损' in msg
    
    def test_take_profit_triggered(self):
        self.rm.open_position('000001', 1000, 10.0)
        self.rm.positions['000001'].current_price = 12.5  # +25%
        triggered, msg = self.rm.check_take_profit('000001')
        assert triggered
        assert '止盈' in msg
    
    def test_take_profit_not_triggered(self):
        self.rm.open_position('000001', 1000, 10.0)
        self.rm.positions['000001'].current_price = 11.0  # +10%
        triggered, _ = self.rm.check_take_profit('000001')
        assert not triggered
    
    def test_check_all_stops(self):
        self.rm.open_position('000001', 1000, 10.0)
        self.rm.open_position('000002', 500, 20.0, sector='金融')
        self.rm.positions['000001'].current_price = 9.0  # 止损
        self.rm.positions['000002'].current_price = 25.0  # 止盈
        alerts = self.rm.check_all_stops()
        assert len(alerts) >= 1
    
    def test_check_stop_nonexistent(self):
        triggered, _ = self.rm.check_stop_loss('999999')
        assert not triggered
    
    # ==================== 风险指标测试 ====================
    
    def test_max_drawdown(self):
        self.rm.daily_values = [100000, 110000, 105000, 95000, 100000]
        dd = self.rm.calculate_max_drawdown()
        # Peak 110000, trough 95000 → dd = 15000/110000 ≈ 13.6%
        assert abs(dd - 15000/110000) < 0.001
    
    def test_max_drawdown_no_data(self):
        assert self.rm.calculate_max_drawdown() == 0.0
    
    def test_sharpe_ratio(self):
        # 稳定上涨 → 正夏普
        self.rm.daily_values = [100000 + i * 100 for i in range(30)]
        sharpe = self.rm.calculate_sharpe_ratio()
        assert sharpe > 0
    
    def test_sharpe_ratio_insufficient_data(self):
        self.rm.daily_values = [100000]
        assert self.rm.calculate_sharpe_ratio() == 0.0
    
    def test_sortino_ratio(self):
        self.rm.daily_values = [100000 + i * 100 for i in range(30)]
        sortino = self.rm.calculate_sortino_ratio()
        assert sortino >= 0
    
    def test_win_rate(self):
        self.rm.trade_history = [
            {'action': 'sell', 'pnl': 100},
            {'action': 'sell', 'pnl': -50},
            {'action': 'sell', 'pnl': 200},
        ]
        assert abs(self.rm.calculate_win_rate() - 2/3) < 0.01
    
    def test_win_rate_no_trades(self):
        assert self.rm.calculate_win_rate() == 0.0
    
    def test_profit_factor(self):
        self.rm.trade_history = [
            {'action': 'sell', 'pnl': 300},
            {'action': 'sell', 'pnl': -100},
        ]
        assert abs(self.rm.calculate_profit_factor() - 3.0) < 0.01
    
    def test_profit_factor_no_losses(self):
        self.rm.trade_history = [
            {'action': 'sell', 'pnl': 300},
        ]
        assert self.rm.calculate_profit_factor() == 99.0
    
    # ==================== 风控锁定测试 ====================
    
    def test_consecutive_loss_lock(self):
        for i in range(5):
            self.rm.open_position(f'00000{i}', 100, 10.0)
            self.rm.close_position(f'00000{i}', price=9.0)
        assert self.rm.is_risk_locked
    
    def test_unlock_risk(self):
        self.rm.is_risk_locked = True
        self.rm.consecutive_losses = 5
        self.rm.unlock_risk()
        assert not self.rm.is_risk_locked
        assert self.rm.consecutive_losses == 0
    
    def test_drawdown_lock(self):
        self.rm.daily_values = [100000]
        self.rm.peak_value = 100000
        self.rm.cash = 84000  # 模拟亏损
        self.rm.record_daily_value()
        assert self.rm.is_risk_locked  # 16% dd > 15% limit
    
    # ==================== 价格更新测试 ====================
    
    def test_update_prices(self):
        self.rm.open_position('000001', 1000, 10.0)
        self.rm.update_prices({'000001': 15.0})
        assert self.rm.positions['000001'].current_price == 15.0
        assert self.rm.positions['000001'].highest_price == 15.0
    
    def test_update_prices_tracks_high(self):
        self.rm.open_position('000001', 1000, 10.0)
        self.rm.update_prices({'000001': 15.0})
        self.rm.update_prices({'000001': 12.0})
        assert self.rm.positions['000001'].highest_price == 15.0
    
    # ==================== 报告测试 ====================
    
    def test_generate_report(self):
        self.rm.open_position('000001', 1000, 10.0, sector='金融')
        self.rm.record_daily_value()
        report = self.rm.generate_report()
        assert report.total_value == 100000  # 刚买入，值不变
        assert report.position_count == 1
        assert report.exposure_pct > 0
        assert '金融' in report.sector_exposure
    
    def test_report_with_trades(self):
        self.rm.open_position('000001', 1000, 10.0)
        self.rm.close_position('000001', price=12.0)
        self.rm.record_daily_value()
        report = self.rm.generate_report()
        assert report.total_pnl == 2000.0
        assert report.win_rate == 1.0
    
    def test_risk_alerts(self):
        self.rm.is_risk_locked = True
        report = self.rm.generate_report()
        assert any('锁定' in a for a in report.risk_alerts)
    
    # ==================== 导出测试 ====================
    
    def test_export_state(self):
        self.rm.open_position('000001', 1000, 10.0)
        state = self.rm.export_state()
        assert state['initial_capital'] == 100000
        assert state['cash'] == 90000
        assert '000001' in state['positions']
        assert state['trade_count'] == 1
    
    # ==================== 边界情况 ====================
    
    def test_exposure_with_empty_portfolio(self):
        assert self.rm.exposure_pct == 0.0
        assert self.rm.cash_pct == 1.0
    
    def test_record_daily_value(self):
        self.rm.record_daily_value()
        assert len(self.rm.daily_values) == 2
        assert self.rm.daily_values[-1] == 100000
    
    def test_win_streak_resets_consecutive_losses(self):
        self.rm.open_position('000001', 100, 10.0)
        self.rm.close_position('000001', price=9.0)  # loss
        assert self.rm.consecutive_losses == 1
        self.rm.open_position('000002', 100, 10.0)
        self.rm.close_position('000002', price=12.0)  # win
        assert self.rm.consecutive_losses == 0
