# A 股量化助手 (StockQuant)

**目标：** 从小白到进阶的量化交易平台  
**技术栈：** Python + AKShare + Pandas + React + Backtrader

---

## 📁 项目结构

```
stock-quant/
├── src/              # 源代码
│   ├── data/         # 数据获取模块
│   ├── strategy/     # 策略引擎
│   ├── backtest/     # 回测模块
│   └── trading/      # 交易模块
├── tests/            # 单元测试
├── data/             # 存储下载的数据
├── notebooks/        # Jupyter 分析笔记
├── docs/             # 文档
├── venv/             # Python 虚拟环境
└── requirements.txt  # 依赖列表
```

---

## 🚀 快速开始

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行数据获取示例
python src/data/fetch_stock_data.py

# 运行测试
python -m pytest tests/
```

---

## 📋 阶段规划

| 阶段 | 功能 | 状态 |
|:---|:---|:---|
| Stage 1 | 数据获取 + 展示 | ✅ 已完成 |
| Stage 1b | 技术指标计算 | ✅ 已完成 |
| Stage 2 | 策略回测引擎 | ✅ 已完成 |
| Stage 3 | 模拟交易 | ✅ 已完成 |
| Stage 4 | 实盘对接 | ⏳ 待开始 |

---

## 📚 Stage 1 - 数据获取

### 目标
- [x] 安装 AKShare
- [ ] 拉取股票历史数据
- [ ] 创建数据展示脚本
- [ ] 基础 K 线数据计算
- [ ] 单元测试覆盖

### AKShare 基础接口

```python
import akshare as ak

# 获取股票历史数据
df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20230101", end_date="20231231")

# 获取实时行情
df = ak.stock_zh_a_spot_em()

# 获取股票列表
df = ak.stock_info_a_code_name()
```

---

## 🌐 访问地址

**本地运行：**
```bash
source venv/bin/activate
streamlit run app.py --server.port 8501
```
→ http://localhost:8501  
**本地访问：** http://localhost:8501

---

**创建时间：** 2026-03-12  
**最后更新：** 2026-03-13 19:59  
**状态：** 项目已启动 🚀
