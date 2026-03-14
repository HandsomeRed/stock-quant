# Stage 2 - 策略回测引擎设计文档

## 📋 目标

实现一个简单的策略回测引擎，支持：
- 均线金叉/死叉策略
- 自定义策略接口
- 回测结果统计
- 可视化展示

---

## 🏗️ 架构设计

```
strategy/
├── base.py           # 策略基类
├── ma_cross.py       # 均线交叉策略
├── backtester.py     # 回测引擎
└── results.py        # 结果分析
```

---

## 📐 策略基类接口

```python
class Strategy(ABC):
    """策略基类"""
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        生成交易信号
        
        Returns:
            Series: 1=买入，-1=卖出，0=持有
        """
        pass
    
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
```

---

## 📊 回测引擎接口

```python
class Backtester:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0
        self.trades = []
    
    def run(self, df: pd.DataFrame, strategy: Strategy) -> Dict:
        """
        运行回测
        
        Returns:
            回测结果字典
        """
        pass
    
    def analyze(self) -> Dict:
        """
        分析回测结果
        
        Returns:
            绩效指标字典
        """
        pass
```

---

## 📈 绩效指标

- **总收益率** = (最终资金 - 初始资金) / 初始资金
- **年化收益率** = (1 + 总收益率)^(252/交易天数) - 1
- **夏普比率** = (年化收益率 - 无风险利率) / 年化波动率
- **最大回撤** = max(历史最高值 - 当前值) / 历史最高值
- **胜率** = 盈利交易次数 / 总交易次数
- **盈亏比** = 平均盈利 / 平均亏损

---

## 🎯 Stage 2 任务清单

- [ ] 创建策略基类 `base.py`
- [ ] 实现均线金叉/死叉策略 `ma_cross.py`
- [ ] 实现回测引擎 `backtester.py`
- [ ] 实现结果分析 `results.py`
- [ ] 编写单元测试
- [ ] 创建回测示例 Notebook

---

## 📅 预计完成时间

- 开发：2-3 小时
- 测试：1 小时
- 文档：30 分钟

---

**创建时间：** 2026-03-12  
**状态：** 待开始
