#!/usr/bin/env python3
"""券商接口抽象层 - Stage 4"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class Order:
    stock_code: str
    order_type: str
    price: float
    quantity: int
    order_id: Optional[str] = None

class BrokerInterface(ABC):
    @abstractmethod
    def login(self, account: str, password: str) -> bool: pass
    
    @abstractmethod
    def place_order(self, order: Order) -> Optional[str]: pass
    
    @abstractmethod
    def get_positions(self) -> Dict: pass
    
    @abstractmethod
    def get_balance(self) -> Dict: pass

class SimulatedBroker(BrokerInterface):
    def __init__(self):
        self.balance = 100000.0
        self.positions = {}
    
    def login(self, account, password): return True
    
    def get_positions(self): return self.positions
    def get_balance(self): return {'available': self.balance}
