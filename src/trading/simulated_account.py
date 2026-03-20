#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟交易模块 - 使用虚拟资金进行实盘模拟
功能：账户管理、委托下单、持仓管理、盈亏计算
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import uuid


class OrderType(Enum):
    """订单类型"""
    BUY = "买入"
    SELL = "卖出"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "待成交"
    FILLED = "已成交"
    CANCELLED = "已撤销"
    REJECTED = "已拒绝"


@dataclass
class Position:
    """持仓"""
    stock_code: str
    stock_name: str
    volume: int  # 持仓数量
    avg_price: float  # 平均成本价
    current_price: float = 0.0  # 当前价
    
    @property
    def market_value(self) -> float:
        """市值"""
        return self.volume * self.current_price
    
    @property
    def cost_value(self) -> float:
        """成本"""
        return self.volume * self.avg_price
    
    @property
    def profit(self) -> float:
        """浮动盈亏"""
        return self.market_value - self.cost_value
    
    @property
    def profit_rate(self) -> float:
        """盈亏比例"""
        if self.cost_value == 0:
            return 0.0
        return self.profit / self.cost_value * 100
    
    def to_dict(self) -> dict:
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'volume': self.volume,
            'avg_price': round(self.avg_price, 2),
            'current_price': round(self.current_price, 2),
            'market_value': round(self.market_value, 2),
            'cost_value': round(self.cost_value, 2),
            'profit': round(self.profit, 2),
            'profit_rate': f"{self.profit_rate:.2f}%"
        }


@dataclass
class Order:
    """委托订单"""
    order_id: str
    stock_code: str
    stock_name: str
    order_type: OrderType
    price: float
    volume: int
    status: OrderStatus = OrderStatus.PENDING
    create_time: datetime = field(default_factory=datetime.now)
    fill_time: Optional[datetime] = None
    fill_price: Optional[float] = None
    fill_volume: int = 0
    
    @property
    def amount(self) -> float:
        """订单金额"""
        return self.price * self.volume
    
    def fill(self, fill_price: float, fill_volume: int):
        """成交"""
        self.status = OrderStatus.FILLED
        self.fill_price = fill_price
        self.fill_volume = fill_volume
        self.fill_time = datetime.now()
    
    def cancel(self):
        """撤销"""
        self.status = OrderStatus.CANCELLED
    
    def to_dict(self) -> dict:
        return {
            'order_id': self.order_id,
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'order_type': self.order_type.value,
            'price': round(self.price, 2),
            'volume': self.volume,
            'amount': round(self.amount, 2),
            'status': self.status.value,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            'fill_time': self.fill_time.strftime('%Y-%m-%d %H:%M:%S') if self.fill_time else '-',
            'fill_price': round(self.fill_price, 2) if self.fill_price else '-',
            'fill_volume': self.fill_volume
        }


@dataclass
class Trade:
    """成交记录"""
    trade_id: str
    order_id: str
    stock_code: str
    stock_name: str
    order_type: OrderType
    price: float
    volume: int
    amount: float
    commission: float  # 手续费
    trade_time: datetime = field(default_factory=datetime.now)
    
    @property
    def net_amount(self) -> float:
        """净金额（含手续费）"""
        if self.order_type == OrderType.BUY:
            return self.amount + self.commission
        else:
            return self.amount - self.commission
    
    def to_dict(self) -> dict:
        return {
            'trade_id': self.trade_id,
            'order_id': self.order_id,
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'order_type': self.order_type.value,
            'price': round(self.price, 2),
            'volume': self.volume,
            'amount': round(self.amount, 2),
            'commission': round(self.commission, 2),
            'net_amount': round(self.net_amount, 2),
            'trade_time': self.trade_time.strftime('%Y-%m-%d %H:%M:%S')
        }


class SimulatedAccount:
    """模拟交易账户"""
    
    COMMISSION_RATE = 0.0003  # 手续费率 万分之三
    MIN_COMMISSION = 5.0  # 最低手续费 5 元
    STAMP_TAX_RATE = 0.001  # 印花税 千分之一（仅卖出收取）
    
    def __init__(self, initial_capital: float = 100000.0):
        self.account_id = str(uuid.uuid4())[:8]
        self.initial_capital = initial_capital
        self.cash = initial_capital  # 可用资金
        self.positions: Dict[str, Position] = {}  # 持仓
        self.orders: List[Order] = []  # 订单列表
        self.trades: List[Trade] = []  # 成交记录
        
    @property
    def total_market_value(self) -> float:
        """总市值"""
        return sum(pos.market_value for pos in self.positions.values())
    
    @property
    def total_assets(self) -> float:
        """总资产"""
        return self.cash + self.total_market_value
    
    @property
    def total_profit(self) -> float:
        """总浮动盈亏"""
        return sum(pos.profit for pos in self.positions.values())
    
    @property
    def total_profit_rate(self) -> float:
        """总盈亏比例"""
        cost = sum(pos.cost_value for pos in self.positions.values())
        if cost == 0:
            return 0.0
        return self.total_profit / cost * 100
    
    def calculate_commission(self, amount: float, order_type: OrderType) -> float:
        """计算手续费"""
        commission = amount * self.COMMISSION_RATE
        commission = max(commission, self.MIN_COMMISSION)
        
        # 卖出加收印花税
        if order_type == OrderType.SELL:
            commission += amount * self.STAMP_TAX_RATE
        
        return commission
    
    def buy(self, stock_code: str, stock_name: str, price: float, volume: int) -> Order:
        """买入委托"""
        # 验证
        if volume <= 0 or volume % 100 != 0:
            raise ValueError("买入数量必须是 100 的整数倍")
        
        amount = price * volume
        commission = self.calculate_commission(amount, OrderType.BUY)
        total_cost = amount + commission
        
        if total_cost > self.cash:
            raise ValueError(f"资金不足，需要 {total_cost:.2f}元，可用 {self.cash:.2f}元")
        
        # 创建订单
        order = Order(
            order_id=str(uuid.uuid4())[:12],
            stock_code=stock_code,
            stock_name=stock_name,
            order_type=OrderType.BUY,
            price=price,
            volume=volume
        )
        
        # 模拟立即成交
        self._fill_order(order, price, volume, commission)
        
        return order
    
    def sell(self, stock_code: str, stock_name: str, price: float, volume: int) -> Order:
        """卖出委托"""
        # 验证
        if volume <= 0 or volume % 100 != 0:
            raise ValueError("卖出数量必须是 100 的整数倍")
        
        if stock_code not in self.positions:
            raise ValueError("不持有该股票")
        
        position = self.positions[stock_code]
        if volume > position.volume:
            raise ValueError(f"持仓不足，持有{position.volume}股，卖出{volume}股")
        
        amount = price * volume
        commission = self.calculate_commission(amount, OrderType.SELL)
        
        # 创建订单
        order = Order(
            order_id=str(uuid.uuid4())[:12],
            stock_code=stock_code,
            stock_name=stock_name,
            order_type=OrderType.SELL,
            price=price,
            volume=volume
        )
        
        # 模拟立即成交
        self._fill_order(order, price, volume, commission)
        
        return order
    
    def _fill_order(self, order: Order, fill_price: float, fill_volume: int, commission: float):
        """订单成交处理"""
        # 更新订单状态
        order.fill(fill_price, fill_volume)
        self.orders.append(order)
        
        # 创建成交记录
        trade = Trade(
            trade_id=str(uuid.uuid4())[:12],
            order_id=order.order_id,
            stock_code=order.stock_code,
            stock_name=order.stock_name,
            order_type=order.order_type,
            price=fill_price,
            volume=fill_volume,
            amount=fill_price * fill_volume,
            commission=commission
        )
        self.trades.append(trade)
        
        # 更新持仓和资金
        if order.order_type == OrderType.BUY:
            self._update_position_buy(order.stock_code, order.stock_name, fill_price, fill_volume)
            self.cash -= (trade.amount + commission)
        else:
            self._update_position_sell(order.stock_code, fill_volume)
            self.cash += (trade.amount - commission)
    
    def _update_position_buy(self, stock_code: str, stock_name: str, price: float, volume: int):
        """更新持仓（买入）"""
        if stock_code in self.positions:
            pos = self.positions[stock_code]
            total_cost = pos.cost_value + price * volume
            total_volume = pos.volume + volume
            pos.avg_price = total_cost / total_volume
            pos.volume = total_volume
            pos.current_price = price
        else:
            self.positions[stock_code] = Position(
                stock_code=stock_code,
                stock_name=stock_name,
                volume=volume,
                avg_price=price,
                current_price=price
            )
    
    def _update_position_sell(self, stock_code: str, volume: int):
        """更新持仓（卖出）"""
        pos = self.positions[stock_code]
        pos.volume -= volume
        
        if pos.volume == 0:
            del self.positions[stock_code]
        else:
            pos.current_price = pos.avg_price  # 卖出后当前价设为成本价
    
    def get_positions(self) -> List[Position]:
        """获取持仓列表"""
        return list(self.positions.values())
    
    def get_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        """获取订单列表"""
        if status:
            return [o for o in self.orders if o.status == status]
        return self.orders
    
    def get_trades(self) -> List[Trade]:
        """获取成交记录"""
        return self.trades
    
    def update_stock_price(self, stock_code: str, price: float):
        """更新股票价格（用于计算浮动盈亏）"""
        if stock_code in self.positions:
            self.positions[stock_code].current_price = price
    
    def get_account_summary(self) -> dict:
        """获取账户概览"""
        return {
            'account_id': self.account_id,
            'initial_capital': round(self.initial_capital, 2),
            'cash': round(self.cash, 2),
            'total_market_value': round(self.total_market_value, 2),
            'total_assets': round(self.total_assets, 2),
            'total_profit': round(self.total_profit, 2),
            'total_profit_rate': f"{self.total_profit_rate:.2f}%",
            'position_count': len(self.positions),
            'trade_count': len(self.trades)
        }
