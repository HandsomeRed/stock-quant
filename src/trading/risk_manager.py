#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险管理模块 - Stage 3.5
提供仓位管理、止损止盈、风险指标计算
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class RiskConfig:
    """风险管理配置"""
    # 仓位管理
    max_position_pct: float = 0.3        # 单只股票最大仓位 30%
    max_total_exposure: float = 0.8      # 总仓位上限 80%
    min_cash_reserve: float = 0.1        # 最低现金保留 10%
    
    # 止损止盈
    stop_loss_pct: float = 0.08          # 止损线 -8%
    take_profit_pct: float = 0.20        # 止盈线 +20%
    trailing_stop_pct: float = 0.05      # 移动止损 5%
    
    # 风险限制
    max_daily_loss_pct: float = 0.05     # 单日最大亏损 5%
    max_drawdown_pct: float = 0.15       # 最大回撤 15%
    max_consecutive_losses: int = 5      # 最大连续亏损次数
    
    # 分散化
    min_stocks: int = 3                  # 最少持仓股票数
    max_stocks: int = 10                 # 最多持仓股票数
    max_sector_pct: float = 0.4          # 单行业最大占比 40%


@dataclass
class PositionInfo:
    """持仓信息"""
    symbol: str
    shares: int
    avg_cost: float
    current_price: float
    highest_price: float = 0.0  # 持仓期间最高价
    entry_time: str = ""
    sector: str = ""
    
    @property
    def market_value(self) -> float:
        return self.shares * self.current_price
    
    @property
    def cost_value(self) -> float:
        return self.shares * self.avg_cost
    
    @property
    def pnl(self) -> float:
        return self.market_value - self.cost_value
    
    @property
    def pnl_pct(self) -> float:
        if self.cost_value == 0:
            return 0.0
        return (self.current_price - self.avg_cost) / self.avg_cost
    
    @property
    def drawdown_from_high(self) -> float:
        if self.highest_price == 0:
            return 0.0
        return (self.highest_price - self.current_price) / self.highest_price


@dataclass
class RiskReport:
    """风险报告"""
    total_value: float = 0.0
    cash: float = 0.0
    positions_value: float = 0.0
    exposure_pct: float = 0.0
    daily_pnl: float = 0.0
    daily_pnl_pct: float = 0.0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    risk_alerts: List[str] = field(default_factory=list)
    position_count: int = 0
    sector_exposure: Dict[str, float] = field(default_factory=dict)


class RiskManager:
    """风险管理器"""
    
    def __init__(self, config: Optional[RiskConfig] = None, initial_capital: float = 100000):
        self.config = config or RiskConfig()
        self.initial_capital = initial_capital
        self.positions: Dict[str, PositionInfo] = {}
        self.cash = initial_capital
        self.trade_history: List[Dict] = []
        self.daily_values: List[float] = [initial_capital]
        self.peak_value = initial_capital
        self.consecutive_losses = 0
        self.is_risk_locked = False
    
    @property
    def total_value(self) -> float:
        positions_value = sum(p.market_value for p in self.positions.values())
        return self.cash + positions_value
    
    @property
    def exposure_pct(self) -> float:
        if self.total_value == 0:
            return 0.0
        positions_value = sum(p.market_value for p in self.positions.values())
        return positions_value / self.total_value
    
    @property
    def cash_pct(self) -> float:
        if self.total_value == 0:
            return 0.0
        return self.cash / self.total_value
    
    # ==================== 仓位计算 ====================
    
    def calculate_position_size(
        self,
        symbol: str,
        price: float,
        signal_strength: float = 1.0
    ) -> int:
        """
        计算建仓数量（A股按手=100股）
        
        Args:
            symbol: 股票代码
            price: 当前价格
            signal_strength: 信号强度 (0-1)
            
        Returns:
            建议买入股数（100的整数倍）
        """
        if self.is_risk_locked:
            return 0
        
        # 最大可用资金
        max_invest = self.total_value * self.config.max_position_pct * signal_strength
        
        # 确保不超过现金
        available = min(max_invest, self.cash * (1 - self.config.min_cash_reserve / self.cash_pct if self.cash_pct > 0 else 0))
        available = max(0, min(available, self.cash - self.total_value * self.config.min_cash_reserve))
        
        # 确保不超过总仓位上限
        current_exposure_value = sum(p.market_value for p in self.positions.values())
        max_additional = self.total_value * self.config.max_total_exposure - current_exposure_value
        available = min(available, max(0, max_additional))
        
        if available <= 0 or price <= 0:
            return 0
        
        # A股最小交易单位 100 股
        shares = int(available / price / 100) * 100
        return max(0, shares)
    
    def calculate_kelly_size(
        self,
        win_rate: float,
        avg_win_pct: float,
        avg_loss_pct: float,
        fraction: float = 0.5
    ) -> float:
        """
        凯利公式计算最优仓位比例
        
        Args:
            win_rate: 胜率
            avg_win_pct: 平均盈利百分比
            avg_loss_pct: 平均亏损百分比（正数）
            fraction: 凯利分数（建议用半凯利 0.5）
            
        Returns:
            建议仓位比例 (0-1)
        """
        if avg_loss_pct == 0 or win_rate <= 0 or win_rate >= 1:
            return 0.0
        
        b = avg_win_pct / avg_loss_pct  # 盈亏比
        kelly = (win_rate * b - (1 - win_rate)) / b
        kelly = max(0, min(kelly * fraction, self.config.max_position_pct))
        return round(kelly, 4)
    
    # ==================== 止损止盈 ====================
    
    def check_stop_loss(self, symbol: str) -> Tuple[bool, str]:
        """检查是否触发止损"""
        pos = self.positions.get(symbol)
        if not pos:
            return False, ""
        
        # 固定止损
        if pos.pnl_pct <= -self.config.stop_loss_pct:
            return True, f"触发止损: {symbol} 亏损 {pos.pnl_pct:.1%} >= {self.config.stop_loss_pct:.0%}"
        
        # 移动止损
        if pos.highest_price > 0 and pos.drawdown_from_high >= self.config.trailing_stop_pct:
            return True, f"触发移动止损: {symbol} 从高点回落 {pos.drawdown_from_high:.1%}"
        
        return False, ""
    
    def check_take_profit(self, symbol: str) -> Tuple[bool, str]:
        """检查是否触发止盈"""
        pos = self.positions.get(symbol)
        if not pos:
            return False, ""
        
        if pos.pnl_pct >= self.config.take_profit_pct:
            return True, f"触发止盈: {symbol} 盈利 {pos.pnl_pct:.1%} >= {self.config.take_profit_pct:.0%}"
        
        return False, ""
    
    def check_all_stops(self) -> List[Tuple[str, str]]:
        """检查所有持仓的止损止盈"""
        alerts = []
        for symbol in list(self.positions.keys()):
            triggered, msg = self.check_stop_loss(symbol)
            if triggered:
                alerts.append((symbol, msg))
                continue
            triggered, msg = self.check_take_profit(symbol)
            if triggered:
                alerts.append((symbol, msg))
        return alerts
    
    # ==================== 风险指标 ====================
    
    def calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        if len(self.daily_values) < 2:
            return 0.0
        
        values = np.array(self.daily_values)
        peaks = np.maximum.accumulate(values)
        drawdowns = (peaks - values) / peaks
        return float(np.max(drawdowns))
    
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.03) -> float:
        """
        计算夏普比率（年化）
        
        Args:
            risk_free_rate: 无风险利率（年化）
        """
        if len(self.daily_values) < 3:
            return 0.0
        
        returns = np.diff(self.daily_values) / self.daily_values[:-1]
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        
        daily_rf = risk_free_rate / 252
        excess_returns = returns - daily_rf
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        return round(float(sharpe), 4)
    
    def calculate_sortino_ratio(self, risk_free_rate: float = 0.03) -> float:
        """计算索提诺比率（只考虑下行风险）"""
        if len(self.daily_values) < 3:
            return 0.0
        
        returns = np.diff(self.daily_values) / self.daily_values[:-1]
        daily_rf = risk_free_rate / 252
        excess_returns = returns - daily_rf
        downside = returns[returns < 0]
        
        if len(downside) == 0 or np.std(downside) == 0:
            return 0.0 if np.mean(excess_returns) <= 0 else 99.0
        
        sortino = np.mean(excess_returns) / np.std(downside) * np.sqrt(252)
        return round(float(sortino), 4)
    
    def calculate_win_rate(self) -> float:
        """计算胜率"""
        closed = [t for t in self.trade_history if t.get('action') == 'sell']
        if not closed:
            return 0.0
        wins = sum(1 for t in closed if t.get('pnl', 0) > 0)
        return round(wins / len(closed), 4)
    
    def calculate_profit_factor(self) -> float:
        """计算盈亏比"""
        closed = [t for t in self.trade_history if t.get('action') == 'sell']
        total_profit = sum(t['pnl'] for t in closed if t.get('pnl', 0) > 0)
        total_loss = abs(sum(t['pnl'] for t in closed if t.get('pnl', 0) < 0))
        
        if total_loss == 0:
            return 99.0 if total_profit > 0 else 0.0
        return round(total_profit / total_loss, 4)
    
    # ==================== 交易操作 ====================
    
    def open_position(
        self,
        symbol: str,
        shares: int,
        price: float,
        sector: str = "",
        timestamp: str = ""
    ) -> Tuple[bool, str]:
        """开仓"""
        cost = shares * price
        if cost > self.cash:
            return False, f"现金不足: 需要 {cost:.2f}, 可用 {self.cash:.2f}"
        
        if symbol in self.positions:
            # 加仓
            pos = self.positions[symbol]
            total_shares = pos.shares + shares
            total_cost = pos.shares * pos.avg_cost + cost
            pos.avg_cost = total_cost / total_shares
            pos.shares = total_shares
            pos.current_price = price
            pos.highest_price = max(pos.highest_price, price)
        else:
            self.positions[symbol] = PositionInfo(
                symbol=symbol,
                shares=shares,
                avg_cost=price,
                current_price=price,
                highest_price=price,
                entry_time=timestamp,
                sector=sector,
            )
        
        self.cash -= cost
        self.trade_history.append({
            'action': 'buy',
            'symbol': symbol,
            'shares': shares,
            'price': price,
            'timestamp': timestamp,
        })
        
        return True, f"买入 {symbol} {shares}股 @ {price:.2f}"
    
    def close_position(
        self,
        symbol: str,
        shares: Optional[int] = None,
        price: float = 0,
        timestamp: str = ""
    ) -> Tuple[bool, str]:
        """平仓"""
        pos = self.positions.get(symbol)
        if not pos:
            return False, f"无持仓: {symbol}"
        
        sell_shares = shares or pos.shares
        sell_shares = min(sell_shares, pos.shares)
        
        revenue = sell_shares * price
        cost_basis = sell_shares * pos.avg_cost
        pnl = revenue - cost_basis
        
        self.cash += revenue
        
        if sell_shares >= pos.shares:
            del self.positions[symbol]
        else:
            pos.shares -= sell_shares
            pos.current_price = price
        
        # 更新连续亏损
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        # 风控锁定检查
        if self.consecutive_losses >= self.config.max_consecutive_losses:
            self.is_risk_locked = True
        
        self.trade_history.append({
            'action': 'sell',
            'symbol': symbol,
            'shares': sell_shares,
            'price': price,
            'pnl': pnl,
            'pnl_pct': pnl / cost_basis if cost_basis > 0 else 0,
            'timestamp': timestamp,
        })
        
        return True, f"卖出 {symbol} {sell_shares}股 @ {price:.2f}, 盈亏: {pnl:+.2f}"
    
    def update_prices(self, prices: Dict[str, float]):
        """更新持仓价格"""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].current_price = price
                self.positions[symbol].highest_price = max(
                    self.positions[symbol].highest_price, price
                )
    
    def record_daily_value(self):
        """记录每日净值"""
        value = self.total_value
        self.daily_values.append(value)
        self.peak_value = max(self.peak_value, value)
        
        # 检查最大回撤锁定
        current_dd = (self.peak_value - value) / self.peak_value if self.peak_value > 0 else 0
        if current_dd >= self.config.max_drawdown_pct:
            self.is_risk_locked = True
    
    def unlock_risk(self):
        """解除风控锁定"""
        self.is_risk_locked = False
        self.consecutive_losses = 0
    
    # ==================== 报告生成 ====================
    
    def generate_report(self) -> RiskReport:
        """生成风险报告"""
        report = RiskReport()
        report.total_value = self.total_value
        report.cash = self.cash
        report.positions_value = sum(p.market_value for p in self.positions.values())
        report.exposure_pct = self.exposure_pct
        report.position_count = len(self.positions)
        
        # 总盈亏
        report.total_pnl = self.total_value - self.initial_capital
        report.total_pnl_pct = report.total_pnl / self.initial_capital if self.initial_capital > 0 else 0
        
        # 每日盈亏
        if len(self.daily_values) >= 2:
            report.daily_pnl = self.daily_values[-1] - self.daily_values[-2]
            report.daily_pnl_pct = report.daily_pnl / self.daily_values[-2] if self.daily_values[-2] > 0 else 0
        
        # 风险指标
        report.max_drawdown = self.calculate_max_drawdown()
        report.sharpe_ratio = self.calculate_sharpe_ratio()
        report.sortino_ratio = self.calculate_sortino_ratio()
        report.win_rate = self.calculate_win_rate()
        report.profit_factor = self.calculate_profit_factor()
        
        # 平均盈亏
        closed = [t for t in self.trade_history if t.get('action') == 'sell']
        wins = [t['pnl'] for t in closed if t.get('pnl', 0) > 0]
        losses = [t['pnl'] for t in closed if t.get('pnl', 0) < 0]
        report.avg_win = np.mean(wins) if wins else 0
        report.avg_loss = np.mean(losses) if losses else 0
        
        # 行业分布
        for pos in self.positions.values():
            sector = pos.sector or '未知'
            report.sector_exposure[sector] = report.sector_exposure.get(sector, 0) + pos.market_value
        
        # 风险警报
        report.risk_alerts = self._check_risk_alerts()
        
        return report
    
    def _check_risk_alerts(self) -> List[str]:
        """检查风险警报"""
        alerts = []
        
        if self.is_risk_locked:
            alerts.append("⚠️ 风控锁定中 - 暂停交易")
        
        if self.exposure_pct > self.config.max_total_exposure:
            alerts.append(f"⚠️ 总仓位 {self.exposure_pct:.0%} 超过上限 {self.config.max_total_exposure:.0%}")
        
        if self.cash_pct < self.config.min_cash_reserve:
            alerts.append(f"⚠️ 现金比例 {self.cash_pct:.0%} 低于保留线 {self.config.min_cash_reserve:.0%}")
        
        max_dd = self.calculate_max_drawdown()
        if max_dd > self.config.max_drawdown_pct * 0.8:
            alerts.append(f"⚠️ 最大回撤 {max_dd:.1%} 接近上限 {self.config.max_drawdown_pct:.0%}")
        
        if self.consecutive_losses >= self.config.max_consecutive_losses - 1:
            alerts.append(f"⚠️ 连续亏损 {self.consecutive_losses} 次，接近锁定阈值")
        
        # 单只股票仓位过高
        for symbol, pos in self.positions.items():
            pos_pct = pos.market_value / self.total_value if self.total_value > 0 else 0
            if pos_pct > self.config.max_position_pct:
                alerts.append(f"⚠️ {symbol} 仓位 {pos_pct:.0%} 超过上限 {self.config.max_position_pct:.0%}")
        
        return alerts
    
    # ==================== 数据导出 ====================
    
    def export_state(self) -> Dict:
        """导出状态"""
        return {
            'initial_capital': self.initial_capital,
            'cash': self.cash,
            'total_value': self.total_value,
            'positions': {
                s: {
                    'shares': p.shares,
                    'avg_cost': p.avg_cost,
                    'current_price': p.current_price,
                    'highest_price': p.highest_price,
                    'sector': p.sector,
                }
                for s, p in self.positions.items()
            },
            'trade_count': len(self.trade_history),
            'daily_values_count': len(self.daily_values),
            'is_risk_locked': self.is_risk_locked,
            'consecutive_losses': self.consecutive_losses,
        }
