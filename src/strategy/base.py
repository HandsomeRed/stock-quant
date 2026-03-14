#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略基类 - 定义策略接口
"""

from abc import ABC, abstractmethod
import pandas as pd
import numpy as np


class Strategy(ABC):
    """策略基类"""
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        生成交易信号
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
            
        Returns:
            Series: 1=买入，-1=卖出，0=持有
        """
        pass
    
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    def description(self) -> str:
        """策略描述"""
        return f"{self.name()} - 量化交易策略"
